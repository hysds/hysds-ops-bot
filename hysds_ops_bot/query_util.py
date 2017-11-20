#!/usr/bin/env python
import os, sys, json, requests, logging, traceback, backoff
from datetime import datetime
from requests.packages.urllib3.exceptions import (InsecureRequestWarning,
                                                  InsecurePlatformWarning)

from conf_util import SettingsConf


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


# settings config
CFG = SettingsConf().cfg


def build_query(ands=None, ors=None, sort_order="desc"):
    """Build ES query."""

    # build musts
    must = []
    if ands is not None:
        for k, v in ands:
            must.append({
                "term": { k: v }
            })

    # build shoulds
    should = []
    if ors is not None:
        for k, v in ors:
            should.append({
                "term": { k: v }
            })

    # build query
    query = {
        "query": {
            "bool": {}
        },
        "sort": [
            {   
                "_timestamp": {
                    "order": sort_order
                }
            }
        ],
        "partial_fields" : {
            "partial" : {
                "exclude" : ["city", "context"],
            }
        }
    }
    if len(must) > 0: query['query']['bool']['must'] = must
    if len(should) > 0:
        if len(must) > 0:
            must.append({'bool': {'should': should}})
        else:
            query['query']['bool']['should'] = should
    return query


@backoff.on_exception(backoff.expo,
                      Exception,
                      max_tries=CFG['BACKOFF_MAX_TRIES'],
                      max_value=CFG['BACKOFF_MAX_VALUE'])
def run_query(url, idx, query):
    """Query ES index."""

    query_url = "{}/{}/_search?search_type=scan&scroll=60&size=100".format(url, idx)
    logger.info("url: {}".format(url))
    logger.info("idx: {}".format(idx))
    logger.info("query: {}".format(json.dumps(query, indent=2)))
    r = requests.post(query_url, data=json.dumps(query))
    r.raise_for_status()
    scan_result = r.json()
    count = scan_result['hits']['total']
    scroll_id = scan_result['_scroll_id']
    hits = []
    while True:
        r = requests.post('%s/_search/scroll?scroll=60m' % url, data=scroll_id)
        res = r.json()
        scroll_id = res['_scroll_id']
        if len(res['hits']['hits']) == 0: break
        hits.extend(res['hits']['hits'])
    return hits


@backoff.on_exception(backoff.expo,
                      Exception,
                      max_tries=CFG['BACKOFF_MAX_TRIES'],
                      max_value=CFG['BACKOFF_MAX_VALUE'])
def job_count(url):
    """Return total number of jobs and counts by status."""

    query = {
        "size": 0,
        "facets": {
            "status": {
                "terms": {
                    "field": "status"
                }
            }
        }
    }
    r = requests.post('%s/job_status-current/job/_search' % url, data=json.dumps(query))
    r.raise_for_status()
    result = r.json()
    counts = { 'total': result['facets']['status']['total'] }
    for terms in result['facets']['status']['terms']:
        counts[terms['term']] = terms['count']

    return {
        'success': True,
        'message': '',
        'counts': counts
    }


@backoff.on_exception(backoff.expo,
                      Exception,
                      max_tries=CFG['BACKOFF_MAX_TRIES'],
                      max_value=CFG['BACKOFF_MAX_VALUE'])
def last_failed(url, job_type):
    """Return last failed job for a specified job type."""

    # query
    query = {
        "query": {
            "bool": {
                "must": [
                    {   
                        "terms": {
                            "status": [ "job-failed" ]
                        }
                    },
                    {
                        "terms": {
                            "resource": [ "job" ]
                        }
                    },
                    {
                        "terms": {
                            "type": [ job_type ]
                        }
                    }
                ]
            }
        },
        "sort": [ {"job.job_info.time_end": { "order":"desc" } } ],
        "_source": [ "job_id", "payload_id", "payload_hash", "uuid",
                     "job.job_info.time_queued", "job.job_info.time_start",
                     "job.job_info.time_end", "error", "traceback" ],
        "size": 1
    }
    r = requests.post('%s/job_status-current/job/_search' % url, data=json.dumps(query))
    r.raise_for_status()
    result = r.json()
    count = result['hits']['total']
    if count == 0: return None
    else:
        latest_job = result['hits']['hits'][0]['_source']
        logging.info("latest job: %s" % json.dumps(latest_job, indent=2))
        return latest_job

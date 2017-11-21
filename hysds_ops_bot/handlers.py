#!/usr/bin/env python
import os, sys, shlex, json, yaml, requests, logging, traceback

from conf_util import SettingsConf
from query_util import job_count, last_failed


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def help_handler(cfg=None, cmd_reg=None):
    """Help handler

    :return (string): return help message
    """

    if cfg is None: cfg = {}
    response = "I don't take orders! But here's what you can ask me:\n"
    for cmd in sorted(cmd_reg):
        response += "*%s*\n" % cmd
    return 'chat.postMessage', { 'text': response }


def status_handler(cluster, cfg=None, cmd_reg=None):
    """Mozart job status handler

    :param cluster (string): cluster
    :return (string): return cluster job status
    """

    if cfg is None: cfg = {}
    url = cfg.get('MOZART_ES_URL', {}).get(cluster, None)
    if url is None:
        return 'No configuration found for cluster "%s". Try again.' % cluster
    counts = job_count(url).get('counts', {})
    response = '*Current job status on "%s" cluster:*\n\n' % cluster
    response += 'Total: %s\n' % counts.get('total', 0)
    response += 'Queued: %s\n' % counts.get('job-queued', 0)
    response += 'Started: %s\n' % counts.get('job-started', 0)
    response += 'Completed: %s\n' % counts.get('job-completed', 0)
    response += 'Failed: %s\n' % counts.get('job-failed', 0)
    response += 'Revoked: %s\n' % counts.get('job-revoked', 0)
    response += 'Deduped: %s\n' % counts.get('job-deduped', 0)
    response += 'Offline: %s\n' % counts.get('job-offline', 0)

    return 'chat.postMessage', { 'text': response }


def query_failed_handler(job_type, cluster, cfg=None, cmd_reg=None):
    """Mozart failed job type query handler

    :param job_type (string): job type to query
    :param cluster (string): cluster
    :return (string): return job ID, error and traceback
    """

    if cfg is None: cfg = {}
    url = cfg.get('MOZART_ES_URL', {}).get(cluster, None)
    if url is None:
        return 'No configuration found for cluster "%s". Try again.' % cluster
    job = last_failed(url, job_type)
    if job is None:
        return 'No failed "%s" job found for cluster "%s". Try again.' % (job_type, cluster)
    response = '*Last failed "%s" job on "%s" cluster:*\n\n' % (job_type, cluster)
    response += 'ID: %s\n' % job['job_id']
    response += 'Error: %s\n' % job['error']
    response += 'Traceback: %s\n' % job['traceback']

    return 'chat.postMessage', { 'text': response }


def transform_handler(cfg=None, cmd_reg=None):
    """Transform handler

    :return (dict): tranform gif
    """

    transform_url = "https://raw.githubusercontent.com/hysds/hysds-ops-bot/master/hysds_ops_bot/megatron_transform.gif"
    response = {
        "attachments": [
            {
                "fallback": "Pesky Autobots!",
                "title": "Pesky Autobots!",
                "image_url": transform_url,
                "color": "#764FA5"
            }
        ],
    }
    return 'chat.postMessage', response


class CommandHandlerException(Exception):
    """Exception class for CommandHandler class."""
    pass


class CommandHandler(object):
    """Class for handling commands."""

    # command registry
    cmd_reg = {
        "help": help_handler,
        "status": status_handler,
        "failed": query_failed_handler,
        "transform": transform_handler,
    }


    def __init__(self, bot_id, slack_client, cfg=None):
        """Construct CommandHandler instance."""

        self._bot_id = bot_id
        self._at_bot =  "<@%s>" % bot_id
        self._sc = slack_client
        self._cfg = SettingsConf().cfg if cfg is None else cfg
        #logger.info("cfg: {}".format(json.dumps(self._cfg, indent=2)))


    def parse_slack_output(self):
        """The Slack Real Time Messaging API is an events firehose.
            this parsing function returns None unless a message is
            directed at the Bot, based on its ID."""
    
        output_list = self._sc.rtm_read()
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self._at_bot in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(self._at_bot)[1].strip().lower(), \
                           output['channel']
        return None, None


    def handle_command(self, command, channel):
        """Receives commands directed at the bot and determines if they
           are valid commands. If so, then acts on the commands. If not,
           returns back what it needs for clarification."""
    
        logger.info("command: %s" % command)
        logger.info("channel: %s" % channel)
     
        # split command
        cmd_list = shlex.split(command)
        cmd = cmd_list[0]
        args = cmd_list[1:]
        logger.info("cmd: %s" % cmd)
        logger.info("args: %s" % args)
    
        # handle commands and get payload
        method = "chat.postMessage"
        if cmd in self.cmd_reg:
            try:
                method, payload = self.cmd_reg[cmd](*args, cfg=self._cfg, cmd_reg=self.cmd_reg)
            except Exception, e:
                payload = {
                    "text": "Error %s:\n%s" % (str(e), self.cmd_reg[cmd].__doc__),
                }
        else:
            payload = {
                "text": "Sure...write some more code then I can do that!",
            }

        # send response
        if method == "chat.postMessage":
            res = self._sc.api_call(method, channel=channel,
                                    as_user=True, **payload)
        elif method == "files.upload":
            res = self._sc.api_call(method, channel=channel,
                                    as_user=True, **payload)
        else:
            raise(CommandHandlerException("Unsupported Slack API call: %s" % method))

        # log result from api call
        logger.info("res: %s" % json.dumps(res, indent=2))

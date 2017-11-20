#!/usr/bin/env python
import os, sys, shlex, json, yaml, requests, logging, traceback

from conf_util import SettingsConf
from query_util import job_count


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def help_handler(cfg=None):
    """Help handler

    :return (string): return help message
    """

    if cfg is None: cfg = {}
    return 'Response for "help" command goes here.'


def status_handler(cluster, cfg=None):
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

    return response


class CommandHandlerException(Exception):
    """Exception class for CommandHandler class."""
    pass


class CommandHandler(object):
    """Class for handling commands."""

    # command registry
    cmd_reg = {
        "help": help_handler,
        "status": status_handler,
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
    
        # handle commands
        if cmd in self.cmd_reg:
            try: response = self.cmd_reg[cmd](*args, cfg=self._cfg)
            except Exception, e:
                response = "Error %s:\n%s" % (str(e), self.cmd_reg[cmd].__doc__)
        else: response = "Sure...write some more code then I can do that!"

        # send response
        self._sc.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

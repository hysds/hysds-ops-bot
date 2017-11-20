#!/usr/bin/env python
import os, sys, shlex, json, yaml, requests, logging, traceback

from conf_util import SettingsConf
from query_util import job_count


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


# get settings
CFG = SettingsConf().cfg


def help_handler():
    """Handler for help command."""

    return 'Response for "help" command goes here.'


class CommandHandlerException(Exception):
    """Exception class for CommandHandler class."""
    pass


class CommandHandler(object):
    """Class for handling commands."""

    cmd_reg = {
        "help": help_handler,
    }

    def __init__(self, bot_id, slack_client, cfg=None):
        """Construct CommandHandler instance."""

        self._bot_id = bot_id
        self._at_bot =  "<@%s>" % bot_id
        self._sc = slack_client
        self._cfg = SettingsConf().cfg if cfg is None else cfg
        logger.info("cfg: {}".format(json.dumps(self._cfg, indent=2)))


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
        if cmd in self.cmd_reg: response = self.cmd_reg[cmd](*args)
        else: response = "Sure...write some more code then I can do that!"

        # send response
        self._sc.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

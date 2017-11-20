#!/usr/bin/env python
import os, sys, json, yaml, requests, logging, traceback

from conf_util import SettingsConf


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


EXAMPLE_COMMAND = "help"

# get settings
CFG = SettingsConf().cfg
logger.info("CFG: {}".format(json.dumps(CFG, indent=2)))


def handle_command(slack_client, command, channel):
    """Receives commands directed at the bot and determines if they
       are valid commands. If so, then acts on the commands. If not,
       returns back what it needs for clarification."""

    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

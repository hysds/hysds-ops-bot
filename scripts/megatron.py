#!/usr/bin/env python
import os
import time
from slackclient import SlackClient

from hysds_ops_bot.conf_util import SettingsConf
from hysds_ops_bot.handlers import CommandHandler, CommandHandlerException


def main(bot_token, bot_id):
    """Main function."""

    # instantiate Slack client and command handler
    slack_client = SlackClient(bot_token)
    ch = CommandHandler(bot_id, slack_client)

    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = ch.parse_slack_output()
            if command and channel:
                ch.handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        raise CommandHandlerException("Connection failed. Invalid Slack token or bot ID?")


if __name__ == "__main__":
    # get bot token and ID from env
    cfg = SettingsConf().cfg
    main(cfg['BOT_TOKEN'], cfg['BOT_ID'])

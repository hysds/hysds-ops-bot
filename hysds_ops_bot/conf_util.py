#!/usr/bin/env python
import os, yaml, logging, traceback

from os_util import norm_path


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


class YamlConfError(Exception):
    """Exception class for YamlConf class."""
    pass


class YamlConf(object):
    """YAML configuration class."""

    def __init__(self, file):
        """Construct YamlConf instance."""

        logger.info("file: {}".format(file))
        self._file = file
        with open(self._file) as f:
            self._cfg = yaml.load(f)

    @property
    def file(self):
        return self._file

    @property
    def cfg(self):
        return self._cfg

    def get(self, key):
        try:
            return self._cfg[key]
        except KeyError as e:
            raise(YamlConfError("Configuration '{}' doesn't exist in {}.".format(key, self._file)))


class SettingsConf(YamlConf):
    """Settings YAML configuration class."""

    def __init__(self, file=None):
        "Construct SettingsConf instance."""

        if file is None:
            file = norm_path(os.path.join(os.path.dirname(__file__), "..",
                                          "conf", "settings.yaml"))
        super(SettingsConf, self).__init__(file)

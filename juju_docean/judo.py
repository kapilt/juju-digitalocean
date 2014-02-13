"""
Juju + DigitalOcean == Judo :-)
--     -      -

CLI Plugin for juju providing digital ocean integration.

See docs @ http://juju-docean.rtfd.org
Src & Issues @ https://github.com/kapilt/juju-docean

Author: Kapil Thangavelu /mail @ kapilt at gmail
License: GPL
"""
import argparse
import dop
import logging
import subprocess
import time
import uuid
import yaml


class Environment(object):

    def __init__(self, config):
        self.config = config

    def status(self):
        pass

    def bootstrap(self):
        pass

    def add_machine(self):
        pass


class Config(object):

    def __init__(self, options):
        self.options = options

    def connect_docean():
        """Connect to digital ocean.
        """

    def connect_environment():
        """Return a websocket connection to the environment.
        """

    def get_env_name():
        """Get the environment name.
        """

    def get_env_conf():
        """Get the environment config file.
        """

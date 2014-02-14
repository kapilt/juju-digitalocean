import os
import yaml

from juju_docean.env import Environment
from juju_docean.exceptions import ConfigError
from juju_docean.provider import factory


class Config(object):

    def __init__(self, options):
        self.options = options

    def connect_provider(self):
        """Connect to digital ocean.
        """
        return factory()

    def connect_environment(self):
        """Return a websocket connection to the environment.
        """
        return Environment(self)

    @property
    def constraints(self):
        return self.options.constraints

    @property
    def series(self):
        return self.options.series

    @property
    def juju_home(self):
        return os.path.expanduser(
            os.environ.get("JUJU_HOME", "~/.juju"))

    def get_env_name(self):
        """Get the environment name.
        """
        if self.options.environment:
            return self.options.environment
        elif os.environ.get("JUJU_ENV"):
            return os.environ['JUJU_ENV']

        env_ptr = os.path.join(self.juju_home, "current-environment")
        if os.path.exists(env_ptr):
            with open(env_ptr) as fh:
                return fh.read().strip()

        with open(self.get_env_conf()) as fh:
            conf = yaml.safe_load(fh.read())
            if not 'default' in conf:
                raise ConfigError("No Environment specified")
            return conf['default']

    def get_env_conf(self):
        """Get the environment config file.
        """
        conf = os.path.join(self.juju_home, 'environments.yaml')
        if not os.path.exists(conf):
            raise ConfigError("Juju environments.yaml not found %s" % conf)
        return conf

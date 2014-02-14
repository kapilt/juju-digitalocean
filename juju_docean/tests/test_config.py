import os
import yaml

from juju_docean.config import Config
from juju_docean.exceptions import ConfigError

from base import Base


class FakeOptions(dict):

    def __getattr__(self, k):
        if not k in self:
            return None
        return self[k]


class ConfigTest(Base):

    def setUp(self):
        self.juju_home = self.mkdir()
        self.change_environment(JUJU_HOME=self.juju_home, JUJU_ENV="")

    def get_config(self, **options):
        return Config(FakeOptions(options))

    def test_get_env_conf(self):
        config = self.get_config()
        self.assertEqual(config.juju_home, self.juju_home)
        self.assertRaises(ConfigError, config.get_env_conf)

        with open(os.path.join(
                self.juju_home, 'environments.yaml'), 'w') as fh:
            fh.write(yaml.safe_dump({'environments': {}}))

    def test_get_env_name(self):
        # Explicit on cli
        config = self.get_config(environment='moon')
        self.assertEqual(config.get_env_name(), 'moon')

        # Default via default
        with open(os.path.join(
                self.juju_home, 'environments.yaml'), 'w') as fh:
            fh.write(yaml.safe_dump({'default': 'mars'}))

        config = self.get_config()
        self.assertEqual(config.get_env_name(), 'mars')

        # Via switch file
        with open(os.path.join(self.juju_home,
                               'current-environment'), 'w') as fh:
            fh.write('pluto')
        config = self.get_config()
        self.assertEqual(config.get_env_name(), 'pluto')

        # Via Environment
        self.change_environment(JUJU_ENV="mercury")
        self.assertEqual(config.get_env_name(), 'mercury')

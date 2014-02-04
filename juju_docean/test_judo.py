import mock
import os
import shutil
import tempfile
import unittest
import yaml

from dop import client as dop


from judo import (
    solve_constraints,
    BaseCommand,
    ConfigError)


class Base(unittest.TestCase):
    def mkdir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        return d

    def change_environment(self, **kw):
        """
        """
        original_environ = dict(os.environ)

        @self.addCleanup
        def cleanup_env():
            os.environ.clear()
            os.environ.update(original_environ)

        os.environ.update(kw)


class ConfigTest(unittest.TestCase):
    pass


class ConstraintTests(unittest.TestCase):

    cases = [
        ("region=nyc, cpu-cores=4, mem=2", (65, 1)),
        ("region=ams, root-disk=100G", (61, 5)),
        ("region=nyc2, mem=24G", (60, 4)),
        ("", (66, 4))]

    def test_constraint_solving(self):
        for constraints, solution in self.cases:
            self.assertEqual(
                solve_constraints(constraints),
                solution)


class BaseCommandTest(unittest.TestCase):

    def setUp(self):
        self.config = mock.MagicMock()
        self.docean = mock.MagicMock()
        self.cmd = BaseCommand(self.config, self.docean)

    def test_get_ssh_keys(self):
        self.docean.all_ssh_keys.return_value = [
            dop.SSHKey(1, 'abc'), dop.SSHKey(32, 'bcd')]
        self.assertEqual(
            self.cmd.get_do_ssh_keys(),
            [1, 32])

    def setup_env(self, conf=None):
        self.docean.all_ssh_keys.return_value = [dop.SSHKey(1, 'abc')]
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self.config.get_env_conf.return_value = f.name
            self.config.get_env_name.return_value = 'docean'
            if conf is None:
                conf = {
                    'environments': {
                        'docean': {
                            'type': 'null',
                            'bootstrap-host': None}}}
            f.write(yaml.safe_dump(conf))
            f.flush()
            self.addCleanup(lambda: os.remove(f.name))

    def test_update_bootstrap_host(self):
        self.setup_env()
        self.cmd.update_bootstrap_host('1.1.1.1')
        with open(self.config.get_env_conf()) as f:
            conf = yaml.safe_load(f.read())['environments']['docean']
        self.assertEqual(conf['bootstrap-host'], '1.1.1.1')

    def test_check_preconditions_okay(self):
        self.setup_env()
        self.assertEqual(self.cmd.check_preconditions(), [1])

    def test_check_preconditions_host_exist(self):
        self.setup_env({
            'environments': {
                'docean': {
                    'type': 'null',
                    'bootstrap-host': '1.1.1.1'}}})
        try:
            self.cmd.check_preconditions()
        except ConfigError, e:
            self.assertIn('already has a bootstrap-host', str(e))
        else:
            self.fail("existing bootstrap-host should raise error")

    def test_check_preconditions_host_invalid_provider(self):
        self.setup_env({
            'environments': {
                'docean': {
                    'type': 'ec2',
                    'bootstrap-host': None}}})
        try:
            self.cmd.check_preconditions()
        except ConfigError, e:
            self.assertIn("provider type is 'ec2' must be 'null'", str(e))

    def test_check_preconditions_host_invalid_env_conf(self):
        self.setup_env({'a': 1})
        try:
            self.cmd.check_preconditions()
        except ConfigError, e:
            self.assertIn('Invalid environments.yaml', str(e))

    def test_check_preconditions_no_named_env(self):
        self.setup_env({'environments': {}})
        try:
            self.cmd.check_preconditions()
        except ConfigError, e:
            self.assertIn(
                "Environment 'docean' not in environments.yaml", str(e))

    def xtest_run_juju(self):
        pass


class BootstrapTest(unittest.TestCase):
    pass


class AddMachineTest(unittest.TestCase):
    pass


class TerminateMachineTest(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

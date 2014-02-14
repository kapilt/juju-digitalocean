import shutil
import subprocess

import os
import yaml


class Environment(object):

    def __init__(self, config):
        self.config = config

    def _run(self, command, env=None):
        args = ['juju', '-e', self.config.get_env_name()]
        args.extend(command)
        return subprocess.check_output(args, env=env)

    def status(self):
        return yaml.safe_load(self._run(['status']))

    def add_machine(self, location):
        return self._run(['add-machine', location])

    def terminate_machines(self, machines):
        cmd = ['terminate-machine', '--force']
        cmd.extend(machines)
        return self._run(cmd)

    def destroy_environment(self):
        return self._run(['destroy-environment'])

    def bootstrap(self):
        return self._run(['bootstrap', '-v'])

    def bootstrap_jenv(self, host):
        """Bootstrap an environment in a sandbox.

        Manual provider config keeps transient state in the form of
        bootstrap-host for its config.

        A temporary JUJU_HOME is used to modify
        """
        env_name = self.config.get_env_name()

        # Prep a new juju home
        boot_home = os.path.join(
            self.config.juju_home, "boot-%s" % env_name)
        os.mkdir(boot_home)
        shutil.copy(self.config.juju_home)

        # Updated env config with the bootstrap host.
        with open(self.get_env_conf()) as fh:
            data = yaml.safe_load(fh.read())
            env_conf = data['environments'].get(env_name)
        env_conf['bootstrap-host'] = host
        with open(os.path.join(
                boot_home, 'environments.yaml'), 'w') as fh:
            fh.write({'environments': env_conf})

        # Change JUJU_ENV
        env = dict(os.environ)
        env['JUJU_HOME'] = boot_home
        self._run(['bootstrap', '-v'], env=env)

        # Copy over the jenv
        shutil.copystat(
            os.path.join(
                boot_home, "environments", "%s.jenv" % env_name),
            os.path.join(
                self.config.juju_home, "environments", "%s.jenv" % env_name))

        # Kill the leftovers
        shutil.rmtree(boot_home)

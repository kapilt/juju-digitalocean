import subprocess
import yaml


class Environment(object):

    def __init__(self, config):
        self.config = config

    def _run(self, command):
        args = ['juju', '-e', self.config.get_env_name()]
        args.extend(command)
        return subprocess.check_output(args)

    def status(self):
        return yaml.safe_load(self._run(['status']))

    def add_machine(self, location):
        return self._run(['add-machine', location])

    def terminate_machines(self, machines):
        cmd = ['terminate-machine', '--force']
        cmd.extend(machines)
        return self._run(cmd)

    def bootstrap(self):
        return self._run(['bootstrap', '-v'])

    def destroy_environment(self):
        return self._run(['destroy-environment'])

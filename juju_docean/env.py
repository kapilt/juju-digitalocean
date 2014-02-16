import httplib
import logging
import shutil
import subprocess
import socket

import os
import yaml

log = logging.getLogger("juju.docean")


class Environment(object):

    def __init__(self, config):
        self.config = config

    def _run(self, command, env=None, capture_err=False):
        if env is None:
            env = dict(os.environ)
        env["JUJU_ENV"] = self.config.get_env_name()
        args = ['juju']
        args.extend(command)
        stderr = None
        if capture_err:
            stderr = subprocess.STDOUT
        log.debug("Running juju command: %s", " ".join(args))
        try:
            return subprocess.check_output(args, env=env, stderr=stderr)
        except subprocess.CalledProcessError, e:
            log.error(
                "Failed to run command %s\n%s",
                ' '.join(args), e.output)
            raise

    def status(self):
        return yaml.safe_load(self._run(['status']))

    def is_running(self):
        """Try to connect the api server websocket to see if env is running.
        """
        name = self.config.get_env_name()
        jenv = os.path.join(
            self.config.juju_home, "environments", "%s.jenv" % name)
        if not os.path.exists(jenv):
            return False
        with open(jenv) as fh:
            data = yaml.safe_load(fh.read())
            if not data:
                return False
            conf = data.get('bootstrap-config')
            if not conf['type'] in ('manual', 'null'):
                return False
        conn = httplib.HTTPSConnection(
            conf['bootstrap-host'], port=17070, timeout=1.2)
        try:
            conn.request("GET", "/")
            return True
        except socket.error:
            return False

    def add_machine(self, location):
        return self._run(['add-machine', location], capture_err=True)

    def terminate_machines(self, machines):
        cmd = ['terminate-machine', '--force']
        cmd.extend(machines)
        return self._run(cmd)

    def destroy_environment(self):
        return self._run(['destroy-environment', "-y",
                          self.config.get_env_name()])

    def bootstrap(self):
        return self._run(['bootstrap', '-v'])

    def bootstrap_jenv(self, host):
        """Bootstrap an environment in a sandbox.

        Manual provider config keeps transient state in the form of
        bootstrap-host for its config.

        A temporary JUJU_HOME is used to modify things.
        """
        env_name = self.config.get_env_name()

        # Prep a new juju home
        boot_home = os.path.join(
            self.config.juju_home, "boot-%s" % env_name)
        os.makedirs(os.path.join(boot_home, 'environments'))
        shutil.copytree(
            os.path.join(self.config.juju_home, 'ssh'),
            os.path.join(boot_home, 'ssh'))

        # Updated env config with the bootstrap host.
        with open(self.config.get_env_conf()) as fh:
            data = yaml.safe_load(fh.read())
            env_conf = data['environments'].get(env_name)
        env_conf['bootstrap-host'] = host
        with open(os.path.join(
                boot_home, 'environments.yaml'), 'w') as fh:
            fh.write(yaml.safe_dump({'environments': {env_name: env_conf}}))

        # Change JUJU_ENV
        env = dict(os.environ)
        env['JUJU_HOME'] = boot_home
        env['JUJU_LOGGING'] = "<root>=DEBUG"
        cmd = ['bootstrap', '--debug']
        if self.config.upload_tools:
            cmd.append("--upload-tools")

        try:
            self._run(cmd, env=env, capture_err=True)
            # Copy over the jenv
            shutil.copy(
                os.path.join(
                    boot_home, "environments", "%s.jenv" % env_name),
                os.path.join(
                    self.config.juju_home,
                    "environments", "%s.jenv" % env_name))
        finally:
            shutil.rmtree(boot_home)

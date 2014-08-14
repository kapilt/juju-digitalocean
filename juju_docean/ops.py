import logging
import time
import subprocess

from juju_docean.exceptions import TimeoutError
from juju_docean import ssh

log = logging.getLogger("juju.docean")


class MachineOp(object):

    def __init__(self, provider, env, params, **options):
        self.provider = provider
        self.env = env
        self.params = params
        self.created = time.time()
        self.options = options

    def run(self):
        raise NotImplementedError()


class MachineAdd(MachineOp):

    timeout = 360
    delay = 8

    def run(self):
        instance = self.provider.launch_instance(self.params)
        self.provider.wait_on(instance)
        instance = self.provider.get_instance(instance.id)
        self.verify_ssh(instance)
        return instance

    def verify_ssh(self, instance):
        """Workaround for manual provisioning and ssh availability.

        Manual provider bails immediately upon failure to connect on
        ssh, we loop to allow the instance time to start ssh.
        """
        max_time = self.timeout + time.time()
        running = False
        while max_time > time.time():
            try:
                if ssh.check_ssh(instance.ip_address):
                    running = True
                    break
            except subprocess.CalledProcessError, e:
                if ("Connection refused" in e.output or
                        "Connection timed out" in e.output or
                        "Connection closed" in e.output or
                        "Connection reset by peer" in e.output):
                    log.debug(
                        "Waiting for ssh on id:%s ip:%s name:%s remaining:%d",
                        instance.id, instance.ip_address, instance.name,
                        int(max_time-time.time()))
                    time.sleep(self.delay)
                else:
                    log.error(
                        "Could not ssh to instance name: %s id: %s ip: %s\n%s",
                        instance.name, instance.id, instance.ip_address,
                        e.output)
                    raise

        if running is False:
            raise TimeoutError(
                "Could not provision id:%s name:%s ip:%s before timeout" % (
                    instance.id, instance.name, instance.ip_address))


class MachineRegister(MachineAdd):

    def run(self):
        instance = super(MachineRegister, self).run()
        try:
            machine_id = self.env.add_machine(
                "ssh:root@%s" % instance.ip_address,
                key=self.options.get('key'))
        except:
            self.provider.terminate_instance(instance.id)
            raise
        return instance, machine_id


class MachineDestroy(MachineOp):

    def run(self):
        self.env.terminate_machines([self.params['machine_id']])
        log.debug("Destroying instance %s", self.params['instance_id'])
        self.provider.terminate_instance(self.params['instance_id'])

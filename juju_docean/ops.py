import logging
import time
import subprocess

from juju_docean.exceptions import TimeoutError

log = logging.getLogger("juju.docean")


class MachineOp(object):

    def __init__(self, provider, env, params):
        self.provider = provider
        self.env = env
        self.params = params
        self.created = time.time()

    def run(self):
        raise NotImplementedError()


class MachineAdd(MachineOp):

    def run(self):
        instance = self.provider.launch_instance(self.params)
        self.provider.wait_on(instance)
        return self.provider.get_instance(instance.id)


class MachineRegister(MachineAdd):

    timeout = 120
    delay = 8

    def run(self):
        instance = super(MachineRegister, self).run()
        # Manual provider bails immediately upon failure to connect
        # on ssh, we loop to allow the instance time to connect.
        max_time = self.timeout + time.time()
        output = None
        while max_time > time.time():
            try:
                output = self.env.add_machine(
                    "ssh:root@%s" % instance.ip_address)
            except subprocess.CalledProcessError, e:
                if ("Connection refused" in e.output or
                        "Connection timed out" in e.output):
                    log.debug("Waiting for ssh on %s", instance.id)
                    time.sleep(self.delay)
                raise
            else:
                break
        if output is None:
            raise TimeoutError(
                "Could not provision instance %s @ %s before timeout" % (
                    instance.id, instance.ip_address))
        return instance, output


class MachineDestroy(MachineOp):

    def run(self):
        self.env.terminate_machines([self.params['machine_id']])
        log.debug("Destroying instance %s", self.params['instance_id'])
        self.provider.terminate_instance(self.params['instance_id'])

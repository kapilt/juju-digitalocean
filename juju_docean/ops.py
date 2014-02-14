import logging

log = logging.getLogger("juju.docean")


class MachineOp(object):

    def __init__(self, provider, env, params):
        self.provider = provider
        self.env = env
        self.params = params

    def run(self):
        raise NotImplementedError()


class MachineAdd(MachineOp):

    def run(self):
        instance = self.provider.create_instance(**self.params)
        self.provider.wait_on(instance)
        return self.provider.get_instance(instance.id)


class MachineRegister(MachineAdd):

    def run(self):
        instance = super(MachineRegister, self).run()
        machine_id = self.env.add_machine("root@%s" % instance.ip_address)
        return instance, machine_id


class MachineDestroy(MachineOp):

    def run(self):
        self.env.terminate_machines([self.params['machine_id']])
        self.provider.terminate_instance(self.params['instance_id'])

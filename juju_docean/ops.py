import logging
import os
import time

log = logging.getLogger("juju.docean")


class MachineOp(object):

    def __init__(self, docean, params):
        self.docean = docean
        self.params = params

    def run(self):
        raise NotImplementedError()


class MachineAdd(MachineOp):

    def run(self):
        droplet = self.docean.create_droplet(**self.params)
        self.wait_on_machines([droplet])
        return self.docean.show_droplet(droplet.id)

    def wait_on(self, event, droplet, event_type=1):
        while 1:
            log.debug("Waiting on %s", droplet.name)
            result = self.docean.request("/events/%s")
            event = result['event']
            if not event['event_type_id'] == event_type:
                # umm.. we're only waiting on creates atm.
                raise ValueError(
                    "Waiting on invalid event type: %d for %s",
                    event['event_type_id'], droplet.name)
            elif event['action_status'] == 'done':
                log.debug("Machine %s ready", droplet.name)
                return
            time.sleep(2)


class MachineRegister(MachineAdd):

    def run(self):
        droplet = super(MachineRegister, self).run()
        self.run_juju(["juju", "add-machine", "root@%s" % droplet.ip_address])
        return droplet


class MachineDestroy(MachineOp):

    def run(self):
        self.run_juju([
            "juju", "terminate-machine", "--force", self.params['machine_id']])
        self.docean.destroy_droplet(self.params['instance_id'])

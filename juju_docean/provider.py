import logging
import os
import time

from dop import client as dop

log = logging.getLogger("juju.docean")


def factory():
    cfg = DigitalOcean.get_config()
    return DigitalOcean(cfg)


class DigitalOcean(object):

    def __init__(self, config, client=None):
        self.config = config
        if client is None:
            self.client = dop.Client(
                config['client_id'],
                config['api_key'])

    @classmethod
    def get_config(cls):
        provider_conf = {}

        client_id = os.environ.get('DO_CLIENT_ID')
        if client_id:
            provider_conf['client_id'] = client_id

        api_key = os.environ.get('DO_API_KEY')
        if api_key:
            provider_conf['api_key'] = api_key

        ssh_key = os.environ.get('DO_SSH_KEY')
        if ssh_key:
            provider_conf['ssh_key'] = ssh_key

        return provider_conf

    def get_ssh_keys(self):
        if 'ssh_key' in self.config:
            return [self.config['ssh_key']]
        return self.client.all_ssh_keys()

    def get_instances(self):
        return self.client.show_all_active_droplets()

    def get_instance(self, instance_id):
        return self.client.show_droplet(instance_id)

    def launch_instance(self, params):
        if not 'virtio' in params:
            params['virtio'] = True
        if not 'private_networking' in params:
            params['private_networking'] = True

    def terminate_instance(self, instance_id):
        self.run_juju([
            "juju", "terminate-machine", "--force", self.params['machine_id']])
        self.client.destroy_droplet(self.params['instance_id'])

    def wait_on(self, instance):
        return self._wait_on(instance['event_id'], instance.name)

    def _wait_on(self, event, name, event_type=1):
        while 1:
            log.debug("Waiting on %s", name)
            result = self.client.request("/events/%s")
            event = result['event']
            if not event['event_type_id'] == event_type:
                # umm.. we're only waiting on creates atm.
                raise ValueError(
                    "Waiting on invalid event type: %d for %s",
                    event['event_type_id'], name)
            elif event['action_status'] == 'done':
                log.debug("Instance %s ready", name)
                return
            time.sleep(2)

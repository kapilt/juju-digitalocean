import logging
import os
import time

from juju_docean.exceptions import ConfigError, ProviderError
from juju_docean.client import Client

log = logging.getLogger("juju.docean")


def factory():
    cfg = DigitalOcean.get_config()
    return DigitalOcean(cfg)


def validate():
    DigitalOcean.get_config()


class DigitalOcean(object):

    def __init__(self, config, client=None):
        self.config = config
        if client is None:
            self.client = Client(
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

        if (not 'client_id' in provider_conf or
                not 'api_key' in provider_conf):
            raise ConfigError("Missing digital ocean api credentials")
        return provider_conf

    def get_ssh_keys(self):
        keys = self.client.get_ssh_keys()
        if 'ssh_key' in self.config:
            keys = [k for k in keys if k.name == self.config['ssh_key']]
        log.debug("Using DO ssh keys: %s" % (", ".join(k.name for k in keys)))
        return keys

    def get_instances(self):
        return self.client.get_droplets()

    def get_instance(self, instance_id):
        return self.client.get_droplet(instance_id)

    def launch_instance(self, params):
        if not 'virtio' in params:
            params['virtio'] = True
        if not 'private_networking' in params:
            params['private_networking'] = True
        if 'ssh_key_ids' in params:
            params['ssh_key_ids'] = map(str, params['ssh_key_ids'])
        return self.client.create_droplet(**params)

    def terminate_instance(self, instance_id):
        self.client.destroy_droplet(instance_id)

    def wait_on(self, instance):
        return self._wait_on(instance.event_id, instance.name)

    def _wait_on(self, event, name, event_type=1):
        loop_count = 0
        while 1:
            time.sleep(8)  # Takes on average 1m for a do instance.
            result = self.client.request("/events/%s" % event)
            event_data = result['event']
            if not event_data['event_type_id'] == event_type:
                raise ValueError(
                    "Waiting on invalid event type: %d for %s",
                    event_data['event_type_id'], name)
            elif event_data['action_status'] == 'done':
                log.debug("Instance %s ready", name)
                return
            elif result['status'] != "OK":
                log.warning("Unknown provider error %s", result)
            else:
                log.debug("Waiting on instance %s %s%%",
                          name, event_data.get('percentage') or '0')
            if loop_count > 8:
                # Its taking a long while (2m+), give the user some
                # diagnostics if in debug mode.
                log.debug("Diagnostics on instance %s event %s",
                          name, result)
            if loop_count > 25:
                # After 3.5m for instance, just bail as provider error.
                raise ProviderError(
                    "Failed to get running instance %s event: %s" % (
                        name, result))
            loop_count += 1

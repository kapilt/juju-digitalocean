import logging
import os
import time

from juju_docean.exceptions import ConfigError, ProviderError
from juju_docean.client import Client
from juju_docean.constraints import init

log = logging.getLogger("juju.docean")


def factory():
    cfg = DigitalOcean.get_config()
    ans = DigitalOcean(cfg)
    init(ans.client)
    return ans


def validate():
    DigitalOcean.get_config()


class DigitalOcean(object):

    def __init__(self, config, client=None):
        self.config = config
        if client is None:
            self.client = Client.connect(config)
        else:
            self.client = client

    @property
    def version(self):
        return self.client.version

    @classmethod
    def get_config(cls):
        provider_conf = {}

        client_id = os.environ.get('DO_CLIENT_ID')
        if client_id:
            provider_conf['DO_CLIENT_ID'] = client_id

        api_key = os.environ.get('DO_API_KEY')
        if api_key:
            provider_conf['DO_API_KEY'] = api_key

        oauth_token = os.environ.get('DO_OAUTH_TOKEN')
        if oauth_token:
            provider_conf['DO_OAUTH_TOKEN'] = oauth_token

        ssh_key = os.environ.get('DO_SSH_KEY')
        if ssh_key:
            provider_conf['DO_SSH_KEY'] = ssh_key

        if (not 'DO_CLIENT_ID' in provider_conf or
                not 'DO_API_KEY' in provider_conf) and \
           not 'DO_OAUTH_TOKEN' in provider_conf:
            raise ConfigError("Missing digital ocean api credentials")
        return provider_conf

    def get_ssh_keys(self):
        keys = self.client.get_ssh_keys()
        if 'DO_SSH_KEY' in self.config:
            keys = [k for k in keys if k.name == self.config['DO_SSH_KEY']]
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
            done, result = self.client.create_done(event, name)
            if done:
                log.debug("Instance %s ready", name)
                return
            else:
                log.debug("Waiting on instance %s", name)
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

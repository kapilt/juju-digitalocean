import os
from dop import client as dop


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
        return self.docean.show_all_active_droplets()

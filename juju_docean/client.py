from juju_docean.exceptions import ProviderAPIError

import requests


class Entity(object):

    @classmethod
    def from_dict(cls, data):
        i = cls()
        i.__dict__.update(data)
        return i


class SSHKey(Entity):
    """SSH Key on digital ocean

    Attributes: id, name
    """


class Droplet(Entity):
    """Instance on digital ocean.

    Attributes: id, name, size_id, image_id, region_id, event_id,
    backups_active, status, ip_address, created_at
    """


class Image(Entity):
    """
    Attributes:, id, name, distribution, slug, public
    """


class Client(object):

    def __init__(self, client_id, api_key):
        self.client_id = client_id
        self.api_key = api_key
        self.api_url_base = 'https://api.digitalocean.com'

    def get_images(self, filter="global"):
        data = self.request("/images")
        return map(Image.from_dict, data.get("images", []))

    def get_url(self, target):
        return "%s%s" % (self.api_url_base, target)

    def get_ssh_keys(self):
        data = self.request("/ssh_keys")
        return map(SSHKey.from_dict, data.get('ssh_keys', []))

    def get_droplets(self):
        data = self.request("/droplets")
        return map(Droplet.from_dict, data.get('droplets', []))

    def get_droplet(self, droplet_id):
        data = self.request("/droplets/%s" % (droplet_id))
        return Droplet.from_dict(data.get('droplet', {}))

    def create_droplet(self, name, size_id, image_id, region_id,
                       ssh_key_ids=None, private_networking=False,
                       backups_enabled=False, virtio=True):
        params = dict(
            name=name, size_id=size_id,
            image_id=image_id, region_id=region_id,
            virtio=bool(private_networking),
            private_networking=bool(private_networking),
            backups_enabled=bool(backups_enabled))

        if ssh_key_ids:
            params['ssh_key_ids'] = ','.join(ssh_key_ids)
        data = self.request('/droplets/new', params=params)
        return Droplet.from_dict(data.get('droplet', {}))

    def destroy_droplet(self, droplet_id, scrub=True):
        data = self.request(
            "/droplets/%s/destroy" % droplet_id,
            params=dict(scrub_data=int(bool(scrub))))
        return data.get('event_id')

    def request(self, target, method='GET', params=None):
        p = params and dict(params) or {}
        p['client_id'] = self.client_id
        p['api_key'] = self.api_key

        headers = {'User-Agent': 'juju/client'}
        url = self.get_url(target)

        if method == 'POST':
            headers['Content-Type'] = "application/json"
            response = requests.post(url, headers=headers, params=p)
        else:
            response = requests.get(url, headers=headers, params=p)

        data = response.json()
        if not data:
            raise ProviderAPIError(response, 'No json result found')

        if data['status'] != "OK":
            raise ProviderAPIError(
                response, data.get('message', data.get('error_message')))

        return data


def main():
    import os
    from juju_docean import constraints
    for instance in Client(os.environ["DO_CLIENT_ID"],
                           os.environ["DO_API_KEY"]).get_droplets():
        for r in constraints.REGIONS:
            if instance.region_id == r['id']:
                break

        print("{:<9} {:<18} {:<8} {:<12} {:<13} {:<10}".format(
            instance.id, instance.name,
            instance.status,
            instance.created_at[:-10],
            r['name'],
            instance.ip_address).strip())

if __name__ == '__main__':
    main()

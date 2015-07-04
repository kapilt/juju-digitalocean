import os

from juju_docean.exceptions import ProviderAPIError

import requests


class Entity(object):

    @classmethod
    def from_dict(cls, data):
        i = cls()
        i.__dict__.update(data)
        i.json_keys = data.keys()
        return i

    def to_json(self):
        return dict([(k, getattr(self, k)) for k in self.json_keys])


class SSHKey(Entity):
    """SSH Key on digital ocean

    Attributes: id, name
    """


class Droplet(Entity):
    """Instance on digital ocean.

    Attributes: id, name, ip_address, created_at, status, size_id, region_id,
                image_id, event_id
    """


class Image(Entity):
    """
    Attributes: id, slug, name, distribution, public, regions
    """


class Size(Entity):
    """
    Attributes: id, name, slug, memory (mb), cpus, disk (gb), transfer (tb),
                price (/mth), regions (v2 only)
    """


class Region(Entity):
    """
    Attributes: id, slug, name, sizes (v2 only), features (v2 only)
    """


class Client(object):

    def get_url(self, target):
        if target.startswith('/'):
            return "%s%s" % (self.api_url_base, target)
        assert target.startswith('https://')
        return target

    def get_sizes(self):
        data = self.request("/sizes")
        return filter(None, map(self.make_size, data.get('sizes', [])))

    def get_regions(self):
        data = self.request("/regions")
        return filter(None, map(self.make_region, data.get("regions", [])))

    def get_images(self):
        data = self.request("/images")
        return filter(None, map(self.make_image, data.get("images", [])))

    def get_droplets(self):
        data = self.request("/droplets")
        return map(self.make_droplet, data.get('droplets', []))

    def get_droplet(self, droplet_id):
        data = self.request("/droplets/%s" % droplet_id)
        return self.make_droplet(data.get('droplet', {}))

    @classmethod
    def connect(cls, config=os.environ):
        oauth_token = config.get('DO_OAUTH_TOKEN')
        if oauth_token:
            return Client_v2(oauth_token)
        client_id = config.get('DO_CLIENT_ID')
        key = config.get('DO_API_KEY')
        if client_id or key:
            if not client_id or not key:
                raise KeyError("Missing api credentials")
            return Client_v1(client_id, key)
        else:
            raise KeyError("Missing api credentials")


class Client_v1(Client):

    version = 1.0

    Transfers_for_sizes = {
        '512mb': 1, '1gb': 2, '2gb': 3, '4gb': 4, '8gb': 5,
        '16gb': 6, '32gb': 7, '48gb': 8, '64gb': 9}

    def __init__(self, client_id, api_key):
        self.client_id = client_id
        self.api_key = api_key
        self.api_url_base = 'https://api.digitalocean.com/v1'

    def get_ssh_keys(self):
        data = self.request("/ssh_keys")
        return map(SSHKey.from_dict, data.get('ssh_keys', []))

    def make_image(self, info):
        return Image.from_dict(
            dict(id=info['id'], slug=info['slug'], name=info['name'],
                 distribution=info['distribution'], public=info['public'],
                 regions=info['region_slugs']))

    def make_region(self, info):
        return Region.from_dict(
            dict(id=info['id'], name=info['name'], slug=info['slug']))

    def make_size(self, info):
        return Size.from_dict(
            dict(id=info['id'], name=info['name'], slug=info['slug'],
                 memory=info['memory'],
                 cpus=info['cpu'], disk=info['disk'],
                 transfer=self.Transfers_for_sizes[info['slug']],
                 price=float(info['cost_per_month'])))

    def make_droplet(self, info):
        attributes = dict(id=info['id'], name=info['name'],
                          image_id=info['image_id'], size_id=info['size_id'])
        for name in ('event_id', 'ip_address', 'created_at', 'status',
                     'region_id', 'event_id'):
            if name in info:
                attributes[name] = info[name]
        return Droplet.from_dict(attributes)

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
        return self.make_droplet(data.get('droplet', {}))

    def create_done(self, event_id, name):
        data = self.request('/events/%s' % event_id)
        event = data.get('event', {})
        if event.get('event_type_id', 1) != 1:
            raise ValueError("Waiting on invalid event type: %d for %s" %
                             (event['event_type_id'], name))
        return event.get('action_status') == 'done', data

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


class Client_v2(Client):

    version = 2.0

    def __init__(self, oauth_token):
        self.oauth_token = oauth_token
        self.api_url_base = 'https://api.digitalocean.com/v2'

    def get_ssh_keys(self):
        data = self.request("/account/keys")
        return map(self.make_ssh_key, data.get('ssh_keys', []))

    def make_ssh_key(self, info):
        return SSHKey.from_dict(
            dict(id=info['id'], name=info['name']))

    def make_image(self, info):
        return Image.from_dict(
            dict(id=info['id'], slug=info['slug'], name=info['name'],
                 distribution=info['distribution'], public=info['public'],
                 regions=info['regions']))

    def make_region(self, info):
        if info['available']:
            return Region.from_dict(
                dict(id=info['slug'], name=info['name'], slug=info['slug'],
                     sizes=info['sizes'], features=info['features']))

    def make_size(self, info):
        if info['available']:
            return Size.from_dict(
                dict(id=info['slug'], name=info['slug'], slug=info['slug'],
                     memory=info['memory'],
                     cpus=info['vcpus'], disk=info['disk'],
                     transfer=info['transfer'],
                     price=info['price_monthly'],
                     regions=info['regions']))

    def make_droplet(self, info):
        attributes = dict(id=info['id'], name=info['name'],
                          status=info['status'], size_id=info['size_slug'],
                          created_at=info['created_at'])
        if 'v4' in info['networks']:
            for network in info['networks']['v4']:
                if network['type'] == 'public':
                    attributes['ip_address'] = network['ip_address']
                    break
        if 'slug' in info['region']:
            attributes['region_id'] = info['region']['slug']
        if 'id' in info['image']:
            attributes['image_id'] = info['image']['id']
        return Droplet.from_dict(attributes)

    def create_droplet(self, name, size_id, image_id, region_id,
                       ssh_key_ids=None, private_networking=False,
                       backups_enabled=False, virtio=True, user_data=None):
        params = dict(
            name=name, size=size_id,
            image=image_id, region=region_id,
            private_networking=bool(private_networking),
            backups=bool(backups_enabled))

        if user_data:
            params['user_data'] = user_data
        if ssh_key_ids:
            params['ssh_keys'] = ssh_key_ids

        data = self.request('/droplets', 'POST', data=params)
        ans = self.make_droplet(data.get('droplet', {}))
        for action in data.get('links', {}).get('actions', []):
            ans.event_id = action['href']
        return ans

    def create_done(self, event_id, name):
        data = self.request(event_id)
        event = data.get('action', {})
        if event.get('type', 'create') != 'create':
            raise ValueError("Waiting on invalid action type: %s for %s" %
                             (event['type'], name))
        completed = event.get('status') == 'completed'
        return completed, event

    def destroy_droplet(self, droplet_id, scrub=True):
        self.request("/droplets/%s" % droplet_id, 'DELETE')

    def request(self, target, method='GET', params=None, data=None):
        p = params and dict(params) or {}
        p['per_page'] = 1000

        headers = {'User-Agent': 'juju/client',
                   'Authorization': 'Bearer ' + self.oauth_token}
        url = self.get_url(target)

        if data is not None:
            response = requests.request(method, url, headers=headers, params=p,
                                        json=data)
        else:
            response = requests.request(method, url, headers=headers, params=p)

        if not (200 <= response.status_code < 300):
            raise ProviderAPIError(response, response.json())

        if method.lower() != 'delete':
            data = response.json()
            if not data:
                raise ProviderAPIError(response, 'No json result found')
            return data


def main():
    import code
    client = Client.connect()
    code.interact(local={'client': client})


if __name__ == '__main__':
    main()

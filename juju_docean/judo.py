"""
Juju + DigitalOcean == Judo :-)
--     -      -

CLI Plugin for juju providing digital ocean integration.

See docs @ http://juju-docean.rtfd.org
Src & Issues @ https://github.com/kapilt/juju-docean

Author: Kapil Thangavelu /mail @ kapilt at gmail
License: GPL
"""
import argparse
import dop
import logging
import time
import yaml


log = logging.getLogger("juju.docean")


class ConfigError(ValueError):
    """ Environments.yaml configuration error.
    """


class PrecheckError(ValueError):
    """ A precondition check failed.
    """


class MissingKey(ValueError):
    """ User is missing ssh keys in digital ocean.
    """


class ConstraintError(ValueError):
    """ Specificed constraint is invalid.
    """

# Record sizes so we can offer constraints around disk, cpu and transfer,
# The v1 api only gives a name (based on ram size) and id.
SIZE_MAP = {
    60: {'name': '32GB', 'mem': 1024*32, 'disk': 320, 'xfer': 7, 'cpu': 12},
    61: {'name': '16GB', 'mem': 1024*16, 'disk': 160, 'xfer': 6, 'cpu': 8},
    62: {'name': '2GB', 'mem': 1024*2, 'disk': 40, 'xfer': 3, 'cpu': 2},
    63: {'name': '1GB', 'mem': 1024, 'disk': 30, 'xfer': 2, 'cpu': 1},
    64: {'name': '4GB', 'mem': 1024*4, 'disk': 60, 'xfer': 4, 'cpu': 2},
    65: {'name': '8GB', 'mem': 1024*8, 'disk': 80, 'xfer': 5, 'cpu': 4},
    66: {'name': '512MB', 'mem': 512, 'disk': 20, 'xfer': 1, 'cpu': 1},
    68: {'name': '96GB', 'mem': 1024*96, 'disk': 960, 'xfer': 10, 'cpu': 24},
    69: {'name': '64GB', 'mem': 1024*64, 'disk': 640, 'xfer': 2, 'cpu': 20},
    70: {'name': '48GB', 'mem': 1024*48, 'disk': 480, 'xfer': 2, 'cpu': 16}}

# Resize disks to mb (silly default in juju-core)
for s in SIZE_MAP.values():
    s['disk'] = s['disk'] * 1024

SIZES_SORTED = (66, 63, 62, 64, 65, 61, 60, 70, 69, 68)

IMAGE_MAP = {
    'precise': 1505447,
    '12.0.4': 1505447,
    'raring': 350076,
    '13.04': 350076,
    'saucy': 1505699,
    '13.10': 1505699}


# Record regions so we can offer nice aliases.
REGIONS = [
    {'name': 'New York 1', 'aliases': ['nyc1', 'nyc'], 'id': 1},
    {'name': 'New York 2', 'aliases': ['nyc2'], 'id': 4},
    {'name': 'Amsterdam 2', 'aliases': ['ams2', 'ams'], 'id': 5}]

DEFAULT_REGION = 4

# afaik, these are unavailable
#    {'name': 'San Francisco 1', 'aliases': ['sfo1']
#    {'name': 'Amsterdam 1 1', 'aliases': ['ams1']

SUFFIX_SIZES = {
    "m": 1,
    "g": 1024,
    "t": 1024 * 1024,
    "p": 1024 * 1024 * 1024}


def converted_size(s):
    q = s[-1].lower()
    size_factor = SUFFIX_SIZES.get(q)
    if size_factor:
        if s[:-1].isdigit():
            return int(s[:-1]) * size_factor
        return None
    elif s.isdigit():
        return int(s)
    return None


def parse_constraints(constraints):
    """
    """
    c = {}
    parts = filter(None, constraints.split(","))
    for p in parts:
        k, v = p.split('=', 1)
        c[k.strip()] = v.strip()

    unknown = set(c).difference(
        set(['region', 'transfer', 'cpu-cores', 'root-disk', 'mem']))
    if unknown:
        raise ConstraintError("Unknown constraints %s" % (" ".join(unknown)))

    if 'mem' in c:
        q = converted_size(c['mem'])
        if q is None:
            raise ConstraintError("Invalid memory size %s" % c['mem'])
        c['mem'] = q

    if 'root-disk' in c:
        d = c.pop('root-disk')
        q = converted_size(d)
        if q is None:
            raise ConstraintError("Unknown root disk size %s" % d)
        c['disk'] = q

    if 'transfer' in c:
        d = c.pop('transfer')
        if not d.isdigit():
            raise ConstraintError("Unknown transfer size %s" % d)
        c['xfer'] = int(d)

    if 'cpu-cores' in c:
        d = c.pop('cpu-cores')
        if not d.isdigit():
            raise ConstraintError("Unknown cpu-cores size %s" % d)
        c['cpu'] = int(d)

    if 'region' in c:
        for r in REGIONS:
            if c['region'] == r['name']:
                c['region'] = r['id']
            elif c['region'] in r['aliases']:
                c['region'] = r['id']
        if not isinstance(c['region'], int):
            raise ConstraintError("Unknown region %s" % c['region'])
    return c


def solve_constraints(constraints):
    """Return machine size and region.
    """
    constraints = parse_constraints(constraints)
    region = constraints.pop('region', DEFAULT_REGION)

    if not constraints:
        return SIZES_SORTED[0], region

    for s in SIZES_SORTED:
        s_info = SIZE_MAP[s]
        matched = True
        for k, v in constraints.items():
            if not s_info.get(k) >= v:
                matched = False
        if matched:
            return s, region

    raise ConstraintError("Could not match constraints %s" % (
        ", ".join(["%s=%s" % (k, v in constraints.items())])))


class MachineOp(object):

    def __init__(self, docean, params):
        self.docean = docean
        self.params = params

    def run(self):
        raise NotImplementedError()


class MachineRemove(MachineOp):

    def run(self):
        pass


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

    def wait_on_machines(self, droplets):
        event_map = dict([(d.event_id, d) for d in droplets])
        while 1:
            log.debug("Waiting on %s",
                      ", ".join(d.name for d in event_map.values()))
            event_ids = event_map.keys()
            # Would be nice to scatter/gather here.
            for evt_id in event_ids:
                result = self.docean.request("/events/%s")
                event = result['event']
                if not event['event_type_id'] == 1:
                    # umm.. we're only waiting on creates atm.
                    raise ValueError(
                        "Waiting on invalid event type: %d for %s",
                        event['event_type_id'], event_map[event['id']].name)
                elif event['action_status'] == 'done':
                    log.debug("Machine %s ready", event_map[evt_id].name)
                    event_map.pop(evt_id)


class BaseCommand(object):

    def solve_constraints(self, constraints):
        size, region = solve_constraints(self.constraints)
        return IMAGE_MAP[self.series], size, region

    def get_do_ssh_keys(self):
        return [k.id for k in self.docean.all_ssh_keys()]

    def update_bootstrap_host(self, ip_address):
        """Update bootstrap-host in named null provider environment.

        Notes this will lose comments and ordering in environments.yaml.
        """
        with open(self.env_conf) as fh:
            conf = yaml.safe_load(fh.read())
            env = conf['environments'][self.env_name]
            env['bootstrap-host'] = ip_address

        with open(self.env_conf, 'w') as fh:
            fh.write(yaml.safe_dump(conf))

    def check_preconditions(self):
        """Check for docean ssh key, and configured environments.yaml.
        """
        keys = self.get_do_ssh_keys()
        if not keys:
            raise ValueError(
                "SSH Public Key must be uploaded to digital ocean")

        with open(self.env_conf) as fh:
            conf = yaml.safe_load(fh.read())
            if not 'environments' in conf:
                raise ConfigError(
                    "Invalid environments.yaml, no 'environments' section")
            if not self.env_name in conf['environments']:
                raise ConfigError(
                    "Environment %r not in environments.yaml" % self.env_name)
            env = conf['environments'][self.env_name]
            if env['type'] != 'null':
                raise ConfigError(
                    "Environment %r provider type is %r must be 'null'" % (
                        self.env_name, env['type']))
            if env['bootstrap-host']:
                raise ConfigError(
                    "Environment %r already has a bootstrap-host" % (
                        self.env_name))
        return keys


class Bootstrap(BaseCommand):
    """
    Actions:
    - Launch a droplet
    - Wait for it to reach running state
    - Update environment in environments.yaml with bootstrap-host address.
    - Bootstrap juju environment

    Preconditions:
    - named environment found in environments.yaml
    - environment provider type is null
    - bootstrap-host must be null
    - at least one ssh key must exist.
    - ? existing digital ocean with matching env name does not exist.
    """
    def run(self):
        keys = self.check_preconditions()
        image, size, region = self.solve_constraints()
        log.debug("Launching droplet")
        params = dict(
            name="%s-0" % self.env_name, image_id=image,
            size_id=size, region_id=region, ssh_key_ids=keys,
            virtio=True, private_networking=True)

        op = MachineOp(self.docean, params)
        droplet = op.run()

        log.debug("Updating environment bootstrap host")
        self.update_bootstrap_host(droplet.ip_address)
        self.juju(["bootstrap", "-e", self.env_name])


class AddMachine(BaseCommand):

    def run(self, options):
        keys = self.check_preconditions()
        image, size, region = solve_constraints(options.constraints)


class TerminateMachine(BaseCommand):

    def run(self, options):
        pass


class DestroyEnvironment(BaseCommand):

    def run(options):
        pass


class Config(object):

    def __init__(self, options):
        self.options = options

    def connect_docean(options):
        pass


def _default_opts(parser):
    parser.add_argument(
        "-e", "--environment", help="Juju environment to operate on")
    parser.add_argument(
        "-v", "--verbose", help="Verbose output")


def _machine_opts(parser):
    parser.add_argument("--constraints")
    parser.add_argument(
        "--series", default="precise", choices=IMAGE_MAP.keys(),
        help="OS Release for machine.")
#    parser.add_argument(
#        "-b", "--enable-backups", help="Enable backups on these nodes")
    parser.add_argument(
        "-n", "--num-machines", type=int, default=1,
        help="Number of machines to allocate")


def setup_parser():
    parser = argparse.ArgumentParser(description="Juju Digital Ocean Plugin")

    subparsers = parser.add_subparser()
    bootstrap = subparsers.add_parser(
        'bootstrap',
        help="Bootstrap an environment")
    _default_opts(bootstrap)
    _machine_opts(bootstrap)

    add_machine = subparsers.add_parser(
        'add-machine',
        help="Add machines to an environment")
    _default_opts(add_machine)
    _machine_opts(add_machine)

    terminate_machine = subparsers.add_parser(
        "terminate-machine",
        help="Terminate machine")
    _default_opts(terminate_machine)

    terminate_environment = subparsers.add_parser(
        'destroy-environment',
        help="Destroy a digital ocean juju environment")
    _default_opts(terminate_environment)

    return parser


def main():
    parser = setup_parser()
    options = parser.parse_args()
    config = Config(options)
    options.command(config)


if __name__ == '__main__':
    main()

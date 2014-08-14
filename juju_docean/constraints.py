from juju_docean.exceptions import ConstraintError

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

# Would be nice to use ubuntu-distro-info, but portability.
SERIES_MAP = {
    '12-04': 'precise',
    '14-04': 'trusty'}


# Record regions so we can offer nice aliases.
REGIONS = [
    {'name': 'New York 1', 'aliases': ['nyc1', 'nyc'], 'id': 1},
    {'name': 'San Francisco 1', 'aliases': ['sfo1', 'sfo'], 'id': 3},
    {'name': 'New York 2', 'aliases': ['nyc2'], 'id': 4},
    {'name': 'Amsterdam 2', 'aliases': ['ams2', 'ams'], 'id': 5},
    {'name': 'Singapore 1', 'aliases': ['sg', 'sg1'], 'id': 6},
    {'name': 'London 1', 'aliases': ['lon1', 'lon', 'london'], 'id': 7}]

DEFAULT_REGION = 4


ARCHES = ['amd64']

# afaics, these are unavailable
#
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
        set(['region', 'transfer', 'cpu-cores', 'root-disk', 'mem', 'arch']))
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

    if 'arch' in c:
        d = c.pop('arch')
        if not d in ARCHES:
            raise ConstraintError("Unsupported arch %s" % d)

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


def get_images(client):
    images = {}
    for i in client.get_images():
        if not i.public:
            continue
        if not i.distribution == "Ubuntu":
            continue

        for s in SERIES_MAP:
            if ("ubuntu-%s-x64" % s) == i.slug:
                images[SERIES_MAP[s]] = i.id
                images[s.replace('-', '.')] = i.id
    return images

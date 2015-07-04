from juju_docean.exceptions import ConstraintError

DEFAULT_REGION = 'nyc3'
REGIONS = ()
SIZES_SORTED = ('512mb',)
SIZE_MAP = {'512mb': {}}

# Would be nice to use ubuntu-distro-info, but portability.
SERIES_MAP = {
    '12-04': 'precise',
    '14-04': 'trusty'}

ARCHES = ['amd64']

# afaics, these are unavailable
#
#    {'name': 'Amsterdam 1 1', 'aliases': ['ams1']

SUFFIX_SIZES = {
    "m": 1,
    "g": 1024,
    "t": 1024 * 1024,
    "p": 1024 * 1024 * 1024}


def init(client, data=None):
    global SIZE_MAP, SIZES_SORTED, REGIONS, DEFAULT_REGION

    if data is not None:
        SIZE_MAP = data['sizes']
        SIZES_SORTED = tuple(sorted(
            SIZE_MAP.keys(), key=lambda id: SIZE_MAP[id].price))
        REGIONS = data['regions']
        return

    # Record sizes so we can offer constraints around disk, cpu and transfer.
    SIZE_MAP = dict((size.id, size) for size in client.get_sizes())
    # Resize disks to mb (silly default in juju-core)
    for s in SIZE_MAP.values():
        s.disk *= 1024

    SIZES_SORTED = tuple(sorted(SIZE_MAP.keys(),
                                key=lambda id: SIZE_MAP[id].price))

    # Record regions so we can offer nice aliases.
    REGIONS = client.get_regions()

    for region in REGIONS:
        if region.slug == 'nyc3':
            DEFAULT_REGION = region.id
            break
    else:
        raise ValueError("Could not find region 'nyc3'")


def size_to_resources(size_id):
    size = SIZE_MAP[size_id]
    return {'Mem': size.memory,
            'CpuCores': size.cpus,
            'Arch': 'amd64',
            'RootDisk': size.disk}


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

    c_out = {}
    if 'mem' in c:
        q = converted_size(c['mem'])
        if q is None:
            raise ConstraintError("Invalid memory size %s" % c['mem'])
        c_out['memory'] = q

    if 'root-disk' in c:
        d = c.pop('root-disk')
        q = converted_size(d)
        if q is None:
            raise ConstraintError("Unknown root disk size %s" % d)
        c_out['disk'] = q

    if 'transfer' in c:
        d = c.pop('transfer')
        if not d.isdigit():
            raise ConstraintError("Unknown transfer size %s" % d)
        c_out['transfer'] = int(d)

    if 'cpu-cores' in c:
        d = c.pop('cpu-cores')
        if not d.isdigit():
            raise ConstraintError("Unknown cpu-cores size %s" % d)
        c_out['cpus'] = int(d)

    if 'arch' in c:
        d = c.pop('arch')
        if not d in ARCHES:
            raise ConstraintError("Unsupported arch %s" % d)

    if 'region' in c:
        for r in REGIONS:
            if c['region'] == r.name:
                c_out['region'] = r.id
                break
            elif c['region'] == r.slug:
                c_out['region'] = r.id
                break
        else:
            raise ConstraintError("Unknown region %s" % c['region'])
    return c_out


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
            if not getattr(s_info, k) >= v:
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

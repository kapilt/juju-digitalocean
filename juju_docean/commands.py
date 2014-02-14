import logging
import uuid
import yaml

from constraints import IMAGE_MAP, solve_constraints
from exceptions import ConfigError
import ops

log = logging.getLogger("juju.docean")


class BaseCommand(object):

    def __init__(self, config, provider):
        self.config = config
        self.provider = provider

    def solve_constraints(self, constraints):
        size, region = solve_constraints(self.constraints)
        return IMAGE_MAP[self.series], size, region

    def get_do_ssh_keys(self):
        return [k.id for k in self.provider.get_ssh_keys()]

    def update_bootstrap_host(self, ip_address):
        """Update bootstrap-host in named null provider environment.

        Notes this will lose comments and ordering in environments.yaml.
        """
        env_conf_path = self.config.get_env_conf()
        with open(env_conf_path) as fh:
            conf = yaml.safe_load(fh.read())
            env = conf['environments'][self.config.get_env_name()]
            env['bootstrap-host'] = ip_address

        with open(env_conf_path, 'w') as fh:
            fh.write(yaml.safe_dump(conf))

    def check_preconditions(self):
        """Check for provider ssh key, and configured environments.yaml.
        """
        keys = self.get_do_ssh_keys()
        if not keys:
            raise ConfigError(
                "SSH Public Key must be uploaded to digital ocean")

        env_name = self.config.get_env_name()
        with open(self.config.get_env_conf()) as fh:
            conf = yaml.safe_load(fh.read())
            if not 'environments' in conf:
                raise ConfigError(
                    "Invalid environments.yaml, no 'environments' section")
            if not env_name in conf['environments']:
                raise ConfigError(
                    "Environment %r not in environments.yaml" % env_name)
            env = conf['environments'][env_name]
            if not env['type'] in ('null', 'manual'):
                raise ConfigError(
                    "Environment %r provider type is %r must be 'null'" % (
                        env_name, env['type']))
            if env['bootstrap-host']:
                raise ConfigError(
                    "Environment %r already has a bootstrap-host" % (
                        env_name))
        return keys


class Bootstrap(BaseCommand):
    """
    Actions:
    - Launch an instance
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
        log.debug("Launching bootstrap host")
        params = dict(
            name="%s-0" % self.env_name, image_id=image,
            size_id=size, region_id=region, ssh_key_ids=keys)

        op = ops.MachineAdd(self.provider, params)
        instance = op.run()

        log.info("Updating environment bootstrap host")
        self.update_bootstrap_host(instance.ip_address)
        self.env.bootstrap()


class AddMachine(BaseCommand):

    def run(self, options):
        keys = self.check_preconditions()
        image, size, region = solve_constraints(options.constraints)
        log.debug("Launching instances")

        params = dict(
            image_id=image, size_id=size, region_id=region, ssh_key_ids=keys)

        for n in range(self.config.num_machines):
            params['name'] = "%s-%s" % (uuid.uuid4().hex)
            self.queue_op(ops.MachineRegister(self.client, **params))

        for (instance, machine_id) in self.iter_results():
            instance, machine_id = self.gather_result()
            log.info("Registered %s as machine %s",
                     instance.ip_address, machine_id)


class TerminateMachine(BaseCommand):

    def run(self, options):
        """Terminate machine in environment.
        """
        self.check_preconditions()

        status = self.environ.status()
        machines = status.get('Machines', {})

        remove = []
        for m in machines:
            if m in options.machines:
                remove.append(
                    {'instance_id': machines[m]['InstanceId'],
                     'machine_id': m})
        droplets = [d.id for d in self.provider.get_instances()]

        def remove_filter(m):
            m['instance_id'] in droplets

        remove = filter(remove_filter,  remove)
        map(self.queue_op, map(remove, ops.MachineDestroy))
        for r in remove:
            self.gather_result()


class DestroyEnvironment(BaseCommand):

    def run(self, options):
        """Destroy environment.
        """
        self.check_preconditions()

        status = self.environ.status()
        machines = status.get('Machines', {})

        remove = []
        for m in machines:
            if m == '0':
                continue
            remove.append(
                {'instance_id': machines[m]['InstanceId'],
                 'machine_id': m})
        instances = [d.id for d in self.provider.get_instances()]

        def remove_filter(m):
            m['instance_id'] in instances

        remove = filter(remove_filter,  remove)
        map(self.queue_op, map(remove, ops.MachineDestroy))
        for i in self.iter_results():
            pass
        self.env.destroy_environment()

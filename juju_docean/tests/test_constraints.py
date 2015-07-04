import json
import os

from base import Base

from juju_docean.client import Region, Size
from juju_docean.constraints import (
    solve_constraints, size_to_resources, init)


class ConstraintTests(Base):

    cases = [
        ("region=nyc1, cpu-cores=4, mem=2", ('8gb', 'nyc1')),
        ("region=ams3, root-disk=100G", ('16gb', 'ams3')),
        ("region=nyc2, mem=24G", ('32gb', 'nyc2')),
        ("region=nyc2, mem=24G, arch=amd64", ('32gb', 'nyc2')),
        ("", ("512mb", 'nyc3'))]

    def setUp(self):
        data_path = os.path.join(os.path.dirname(__file__), 'constraints.json')
        with open(data_path) as fh:
            data = json.loads(fh.read())
            data['sizes'] = dict(
                [(k, Size.from_dict(v)) for k, v in data['sizes'].items()])
            data['regions'] = map(Region.from_dict, data['regions'])
            init(None, data=data)

    def test_constraint_solving(self):
        for constraints, solution in self.cases:
            self.assertEqual(
                solve_constraints(constraints),
                solution)

    def test_sizes_to_resource(self):
        self.assertEqual(
            size_to_resources('1gb'),
            {'Mem': 1024,
             'CpuCores': 1,
             'Arch': 'amd64',
             'RootDisk': 30720})

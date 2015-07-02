from base import Base

from juju_docean.client import Client
from juju_docean.constraints import solve_constraints, init


class ConstraintTests(Base):

    cases = [
        ("region=nyc1, cpu-cores=4, mem=2", ('8gb', 'nyc1')),
        ("region=ams3, root-disk=100G", ('16gb', 'ams3')),
        ("region=nyc2, mem=24G", ('32gb', 'nyc2')),
        ("region=nyc2, mem=24G, arch=amd64", ('32gb', 'nyc2')),
        ("", ("512mb", 'nyc3'))]

    def setUp(self):
        init(Client.connect())

    def test_constraint_solving(self):
        for constraints, solution in self.cases:
            self.assertEqual(
                solve_constraints(constraints),
                solution)

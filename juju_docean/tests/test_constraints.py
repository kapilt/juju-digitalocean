from base import Base

from juju_docean.constraints import solve_constraints


class ConstraintTests(Base):

    cases = [
        ("region=nyc, cpu-cores=4, mem=2", (65, 1)),
        ("region=ams, root-disk=100G", (61, 5)),
        ("region=nyc2, mem=24G", (60, 4)),
        ("region=nyc2, mem=24G, arch=amd64", (60, 4)),
        ("", (66, 4))]

    def test_constraint_solving(self):
        for constraints, solution in self.cases:
            self.assertEqual(
                solve_constraints(constraints),
                solution)

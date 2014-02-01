import unittest

from judo import solve_constraints


class ConfigTest(unittest.TestCase):
    pass


class ConstraintTests(unittest.TestCase):

    cases = [
        ("region=nyc, cpu-cores=4, mem=2", (65, 1)),
        ("region=ams, root-disk=100G", (61, 5)),
        ("region=nyc2, mem=24G", (60, 4)),
        ("", (66, 4))]

    def test_constraint_solving(self):
        for constraints, solution in self.cases:
            self.assertEqual(
                solve_constraints(constraints),
                solution)


class BaseOpTest(unittest.TestCase):
    pass


class BootstrapTest(unittest.TestCase):
    pass


class AddMachineTest(unittest.TestCase):
    pass


class TerminateMachineTest(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

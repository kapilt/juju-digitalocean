from base import Base

import os
import unittest

from juju_docean.client import Client
from juju_docean.constraints import (
    solve_constraints, images, IMAGE_MAP)


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

    @unittest.skipIf(
        Base.have_do_api_keys(),
        "Image cache verification needs DO client env variables")
    def test_image_cache(self):
        c = Client(os.environ['DO_CLIENT_ID'],
                   os.environ['DO_API_KEY'])
        self.assertEqual(images(c), IMAGE_MAP)

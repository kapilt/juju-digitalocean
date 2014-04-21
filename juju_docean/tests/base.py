import os
import shutil
import tempfile
import unittest


class Base(unittest.TestCase):
    def mkdir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        return d

    def change_environment(self, **kw):
        """
        """
        original_environ = dict(os.environ)

        @self.addCleanup
        def cleanup_env():
            os.environ.clear()
            os.environ.update(original_environ)

        os.environ.update(kw)

    @staticmethod
    def have_do_api_keys():
        return bool(
            'DO_CLIENT_ID' in os.environ
            and
            'DO_API_KEY' in os.environ)

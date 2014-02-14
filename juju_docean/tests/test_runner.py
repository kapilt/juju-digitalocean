
from juju_docean.runner import Runner
from base import Base


class FakeOp(object):

    def run(self):
        return 1


class FakeBadOp(object):

    def run(self):
        return ValueError("Bad")


class RunnerTest(Base):

    def test_auto_runner(self):
        runner = Runner()
        runner.queue_op(FakeOp())
        runner.queue_op(FakeOp())
        results = list(runner.iter_results())
        self.assertEqual(results, [1, 1])
        self.assertFalse(runner.started)

    def test_runner(self):
        runner = Runner()
        runner.queue_op(FakeOp())
        runner.queue_op(FakeOp())
        runner.queue_op(FakeBadOp())
        runner.start(2)
        results = list(runner.iter_results())
        self.assertEqual(len(results), 2)
        runner.stop()

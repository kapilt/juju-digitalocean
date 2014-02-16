"""
Thread based concurrency around bulk ops. do api is sync
"""

import logging
from Queue import Queue, Empty
import threading


log = logging.getLogger("juju.docean")


class Runner(object):

    DEFAULT_NUM_RUNNER = 4

    def __init__(self):
        self.jobs = Queue()
        self.results = Queue()
        self.job_count = 0
        self.runners = []
        self.started = False

    def queue_op(self, op):
        self.jobs.put(op)
        self.job_count += 1

    def iter_results(self):
        auto = not self.started

        if auto:
            self.start(min(self.DEFAULT_NUM_RUNNER, self.job_count))

        for i in range(self.job_count):
            self.job_count -= 1
            result = self.gather_result()
            if isinstance(result, Exception):
                continue
            yield result

        if auto:
            self.stop()

    def gather_result(self):
        return self.results.get()

    def start(self, count):
        for i in range(count):
            runner = OpRunner(self.jobs, self.results)
            runner.daemon = True
            self.runners.append(runner)
            runner.start()
        self.started = True

    def stop(self):
        for runner in self.runners:
            runner.join()
        self.started = False


class OpRunner(threading.Thread):

    def __init__(self, ops, results):
        self.ops = ops
        self.results = results
        super(OpRunner, self).__init__()

    def run(self):
        while 1:
            try:
                op = self.ops.get(block=False)
            except Empty:
                op = None
            if op is None:
                return
            try:
                result = op.run()
            except Exception, e:
                log.exception("Error while processing op %s", op)
                result = e
            self.results.put(result)

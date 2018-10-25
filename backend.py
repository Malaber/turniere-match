from collections import namedtuple
from queue import Queue
from threading import Thread

Task = namedtuple('Task', ['func', 'params', 'callback'])


def execute_function(function, callback):
    pass


class QueueWorker(Thread):
    def __init__(self, turniere_instances):
        super()
        self.turniere_instances = turniere_instances
        self.queue = Queue()

    def enqueue(self, event):
        self.queue.put_nowait(event)

    def run(self):
        while True:
            task = self.queue.get()
            print(task)
            # mark done
            self.queue.task_done()

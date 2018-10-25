import time
from collections import namedtuple
from queue import Queue
from threading import Thread

from requests.exceptions import ConnectionError

Match = namedtuple('Match', ['mid', 'score1', 'score2', 'is_live'])


class Worker(Thread):
    def __init__(self, instance):
        Thread.__init__(self)
        self.instance = instance
        self.queue = Queue()
        self.retry_interval = 1
        self.done = False

    def run(self):
        while True:
            match = self.queue.get()
            print('Synchronizing {}'.format(match))
            while True:
                try:
                    self.instance.login()
                    if type(match) == str:
                        self.instance.next_group_matches()
                    elif type(match) == int:
                        self.instance.next_stage_matches(str(match))
                    else:
                        self.instance.submit_results(
                            match.mid,
                            match.score1,
                            match.score2,
                            match.is_live
                        )
                    break
                except Exception as e:
                    print(
                        'Couldn\'t connect to remote instance ({}),'
                        ' retrying in {}s'.format(e, self.retry_interval)
                    )
                    time.sleep(self.retry_interval)
            self.queue.task_done()

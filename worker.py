import time
from collections import namedtuple
from queue import Queue
from threading import Thread

Match = namedtuple(
    'Match',
    ['mid', 'matchscore1', 'matchscore2', 'score1', 'score2', 'is_live']
)


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
            print(f'Synchronizing {match}')
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
                        f'Couldn\'t connect to remote instance ({e}),'
                        f' retrying in {self.retry_interval}s'
                    )
                    time.sleep(self.retry_interval)
            self.queue.task_done()

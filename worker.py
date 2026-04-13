import logging
import time
from collections import namedtuple
from queue import Queue
from threading import Thread

Action = namedtuple('Action', ['type', 'data'])
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
        while not self.done:
            action = self.queue.get()
            logging.info(f'Synchronizing {action}')
            while True:
                try:
                    self.instance.login()
                    if action.type == 'next_group_matches':
                        self.instance.next_group_matches()
                        break
                    elif action.type == 'next_stage_matches':
                        self.instance.next_stage_matches(action.data)
                        break
                    elif action.type == 'submit_results':
                        self.instance.submit_results(action.data)
                        break
                    elif action.type == 'stop_group_stage':
                        self.instance.stop_group_stage(action.data)
                        break
                    elif action.type == 'update_team_name':
                        self.instance.update_team_name(action.data[0], action.data[1])
                        break
                    elif action.type == 'set_timer_end':
                        self.instance.set_timer_end(action.data)
                        break
                    elif action.type == 'create_beamer':
                        self.instance.create_beamer(*action.data)
                        break
                    elif action.type == 'update_beamer':
                        self.instance.update_beamer_by_name(action.data[0], action.data[1])
                        break
                    elif action.type == 'delete_beamer':
                        self.instance.delete_beamer_by_name(action.data)
                        break
                    else:
                        raise Exception('This shouldn\'t happen')
                except Exception as e:
                    logging.info(
                        f'Couldn\'t connect to remote instance ({e}),'
                        f' retrying in {self.retry_interval}s'
                    )
                    time.sleep(self.retry_interval)
            self.queue.task_done()

    def stop(self):
        logging.info('Stopping worker')
        self.done = True

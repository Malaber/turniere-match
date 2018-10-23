from threading import Thread


class BackendThread(Thread):
    def __init__(self, queue, session):
        super()
        self.queue = queue
        self.session = session

    def run(self):
        while True:
            request = self.queue.get()
            self.session.send(request)

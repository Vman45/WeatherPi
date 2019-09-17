from threading import Thread
from AuriolStorage import AuriolStorage
from time import sleep
import requests
import json

class Uploader(Thread):

    def __init__(self, endpoint, database, logger):
        #Inherit from Thread
        Thread.__init__(self)

        self.TOKEN = ''

        self.logger = logger
        self.endpoint = endpoint
        self.database = database
        self.queue = []

        self.stopped = False


    def run(self):

        self.logger.info('Starting upload handler')
        storage = AuriolStorage(self.database)

        while not self.stopped:
            if len(self.queue) > 0:
                self.fillData(self.queue[0])
                uploadState = self.upload(self.queue[0])
                if not uploadState: storage.push(self.queue[0])

                del self.queue[0]

            elif storage.size() != 0:
                data = storage.front()
                self.fillData(data)
                uploadState = self.upload(data)
                if uploadState: storage.pop()

            sleep(1)

        storage.close()
        self.logger.info('Stopping upload handler')


    def upload(self, data):
        try:
            r = requests.post(
                self.endpoint,
                json=data,
                timeout = 5
            )
        except requests.exceptions.RequestException as e:
            self.logger.info(e)
            return False

        if r.status_code == 409:
            self.logger.info('Possible format error with {:s}\nDeleting from the queue'.format(json.dumps(data)))
            return True

        if r.status_code != 201:
            self.logger.info('Error during upload, status code: {:d}'.format(r.status_code))
            return False

        self.logger.info('Uploaded correctly')
        return True


    def fillData(self, data):
        data['token'] = self.TOKEN
        data['humidity'] = 0


    def stop(self):
        self.stopped = True
        self.join()


    def push(self, data):
        self.queue.append(data)
import time
from collections import defaultdict
from threading import Thread, Lock

import redis
from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)
api = Api(app)
cache = redis.Redis(host='redis', port=6379)
locks = defaultdict(Lock)


def process_request(resource_id):
    '''Does some very time-consuming stuff here'''

    time.sleep(10)
    return 'content of {}'.format(resource_id)


def threaded_task(resource_id):
    '''
    Run the time-consuming function and cache the result.
    Use lock for the specific resource, to avoid race condition.
    '''

    locks[resource_id].acquire()
    cache.set(resource_id, process_request(resource_id), ex=60)
    locks[resource_id].release()


def start_task(resource_id):
    '''Run the task in a background thread'''

    thread = Thread(target=threaded_task, args=(resource_id,), daemon=True)
    thread.start()
    return resource_id


class SyncHandler(Resource):

    def get(self, resource_id):
        '''This synchronous request will take ~10s to process'''

        value = process_request(resource_id)
        return {'value': value}, 200


class AsyncHandler(Resource):

    def post(self, resource_id):
        '''Trigger processing of the job in the background'''

        job_id = start_task(resource_id)
        return {'job': '/async/{}'.format(job_id)}, 202

    def get(self, resource_id):
        '''Check if the job is ready and return result'''

        value = cache.get(resource_id)
        if value is None:
            return {'error': 'Not ready or expired'}, 204
        return {'value': value.decode('utf-8')}, 200

    def delete(self, resource_id):
        cache.delete(resource_id)
        return None, 200


api.add_resource(SyncHandler, '/sync/<string:resource_id>')
api.add_resource(AsyncHandler, '/async/<string:resource_id>')


if __name__ == '__main__':
    app.run(debug=True)
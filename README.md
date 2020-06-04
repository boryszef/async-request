# Asynchronous handling of heavy requests

This is proof-of-concept example how a long request can be replaced by a background task.

## The problem

Consider this scenario: GET request on http://172.17.0.1:5000/sync/foo takes couple of
minutes to complete. Besides the fact that it is a bad programming practice, the longer
the request, the higher is the risk of timeouts and other network problems.

## Solution

To avoid timeouts and broken connection the following mechanism is implemented:
POST request to http://172.17.0.1:5000/async/foo triggers processing of the request in
the background and returns path to the results (when they are ready):

```json
{"job": "/async/foo"}
```

GET request on http://172.17.0.1:5000/async/foo returns 204, when the job is not ready
yet or has not been scheduled at all. When the task finishes, it returns 200 and the
content.

Additionally, DELETE request on http://172.17.0.1:5000/async/foo can be used to trash
the results.

# Implementation

The POST request triggers a background thread that processes the request and stores it
in Redis with a key that is related to the path sent in the response to the user; for instance
if the path is `/async/foo` then the Redis key will be `foo`. GET request checks if the
key exists and based on that returns the response or the status 204.

The value Redis has an expiration time, so it will be removed even if the user does not
send the DELETE request.

The background task uses lock mechanism to make sure that another thread does not process
the request on the same resource (and the key).
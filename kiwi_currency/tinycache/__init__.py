""" 
    TODO: Implement logging with config from the application
    TODO: Implement method init_app. See https://flask.palletsprojects.com/en/1.1.x/extensiondev/
"""

from time import time
import threading
import functools


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)

    return _wrap


class TinyCache:
    def __init__(self):
        self._default_expiry = 7 * 24 * 60 * 60
        self._cache = {}

    @synchronized
    def set(self, key, value, expiry=None):
        expiry = expiry if expiry is not None else self._default_expiry
        self._cache[key] = {
            "value": value,
            "expiry": int(time()) + expiry if expiry else 0,
        }

    @synchronized
    def invalidate(self, key):
        self._cache.pop(key, None)

    @synchronized
    def invalidate_all(self):
        self._cache = {}

    @synchronized
    def get(self, key):
        if key not in self._cache:
            return None

        record = self._cache.get(key)
        expiry_time = record.get("expiry")
        if 0 < expiry_time < int(time()):
            self.invalidate(key)
            return None
        else:
            return record.get("value")
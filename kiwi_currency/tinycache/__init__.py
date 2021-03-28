import functools
import threading
from datetime import datetime


def synchronized(wrapped):
    """
    Wrapper to make a method synchronized
    or therad safe.
    """
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)

    return _wrap


def utc_epoch():
    return int(datetime.utcnow().timestamp())


class TinyCache:
    """
    Used as a in-memory cache with expiration
    period for the cache records.
    """

    def __init__(self):

        # init of the cache with empty dict
        self._cache = {}

    @synchronized
    def set(self, key, value, expiry=None, absolute=True):
        """
        Method to set a value in the cache.

        Parameters
        ----------
        key : string
            The key for the cache record
        value : any
            The value for the cache record
        expiry : integer
            Number of seconds
        absolute : bool
            If the expiration period is absolute or relative.

        """
        if expiry is None:
            expiry_time = 0
        else:
            expiry_time = int(expiry) + int(not absolute) * utc_epoch()

        self._cache[key] = {"value": value, "expiry": expiry_time}

    @synchronized
    def invalidate(self, key):
        """
        Method to invalidate a cache entry.

        Parameters
        ----------
        key : string
            The cache key

        """
        self._cache.pop(key, None)

    @synchronized
    def invalidate_all(self):
        """
        Method to clear the cache.
        """
        self._cache = {}

    @synchronized
    def get(self, key):
        """
        Method to get the value of certain cache record
        by the key.
        If key is found inside the cache, we also check the
        expiration time. In case of expired cache, we invalidate the cache.

        Parameters
        ----------
        key : string
            The cache key

        Returns
        -------
        any
            The value stored for the key.
            If not found or not valid, None is returned.
        """
        if key not in self._cache:
            return None

        record = self._cache.get(key)
        expiry_time = record.get("expiry", 0)

        if 0 < expiry_time and expiry_time < utc_epoch():
            self.invalidate(key)
            return None
        else:
            return record.get("value")

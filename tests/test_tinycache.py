import time

from currency_convertor.tinycache import TinyCache, utc_epoch


def test_expiry_time():
    cache = TinyCache()

    # absolute expiration time
    cache.set("a", 120, expiry=utc_epoch() + 2)
    time.sleep(4)
    assert cache.get("a") == None


def test_invalidate():
    cache = TinyCache()

    cache.set("a", 120)
    assert cache.get("a") == 120

    cache.invalidate("a")
    assert cache.get("a") == None


def test_invalidate_all():
    cache = TinyCache()

    cache.set("a", 120)
    cache.set("b", 220)

    cache.invalidate_all()
    assert not bool(cache._cache)


def test_get_with_valid_expiry_time():
    cache = TinyCache()

    # relative expiration time
    cache.set("a", 120, expiry=10, absolute=False)
    time.sleep(2)

    assert cache.get("a") == 120

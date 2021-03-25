import time

from kiwi_currency.tinycache import TinyCache


def test_expiry_time():
    cache = TinyCache()

    cache.set("a", 120, expiry=2.0)
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

    cache.set("a", 120, expiry=10)
    time.sleep(2)

    assert cache.get("a") == 120

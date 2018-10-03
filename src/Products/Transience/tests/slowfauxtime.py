import time as origtime


epoch = origtime.time()


def time():
    """Fake timer -- returns time 60 x faster than normal time."""
    return (origtime.time() - epoch) * 60


def sleep(duration):
    """Fake sleep -- sleep for 1/60 the time specifed."""
    origtime.sleep(duration / 60)

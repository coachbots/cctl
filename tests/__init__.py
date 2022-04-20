import asyncio


def async_test(coro):
    """Wraps a test function in a new event loop."""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return coro(*args, **kwargs)
        finally:
            loop.close()
    return wrapper

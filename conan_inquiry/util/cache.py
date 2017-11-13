import os
from datetime import datetime, timedelta
from json import JSONDecodeError, dump as json_dump, load as json_load
from threading import Lock
from typing import Callable, Union, Dict, Any


class Cache:
    """This class provides a simple cache with "expiry-on-retrieval"""

    current_cache = None

    def __init__(self, file: str = None):
        self.file = file if file is not None else os.path.join(os.getcwd(), '.cache')
        self.cache = None
        self.lock = Lock()

    def __enter__(self):
        with self.lock:
            self.__class__.current_cache = self
            if os.path.exists(self.file):
                try:
                    self.cache = json_load(open(self.file, 'r'))
                except JSONDecodeError:
                    self.cache = dict()
            else:
                self.cache = dict()

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.lock:
            os.makedirs(os.path.dirname(self.file), exist_ok=True)
            json_dump(self.cache, open(self.file, 'w'))

    def set(self, key: str, value: Union[str, int, float, Dict[str, Any]], context: str = None):
        """Insert or update a value"""

        with self.lock:
            if context is None:
                self.cache[key] = dict(value=value, time=datetime.now().timestamp())
            else:
                if context not in self.cache:
                    self.cache[context] = dict()
                self.cache[context][key] = dict(value=value, time=datetime.now().timestamp())

    def _has(self, key: str, maxage: timedelta, context: str = None) -> bool:
        if context is None:
            if key not in self.cache:
                return False
            time = self.cache[key]['time']
        else:
            if context not in self.cache or key not in self.cache[context]:
                return False
            time = self.cache[context][key]['time']
        return (datetime.now() - maxage) < datetime.fromtimestamp(time)

    def has(self, key: str, maxage: timedelta, context: str = None) -> bool:
        """Check if we have a not-yet-expired value"""

        with self.lock:
            return self._has(key, maxage, context)

    def get(self, key: str, maxage: timedelta, context: str = None,
            func: Callable[[], object] = None):
        """Retrieve, if possible, a value. Optionally compute and set it if not available"""

        with self.lock:
            if not self._has(key, maxage, context):
                if func is None:
                    return None
                else:
                    value = func()
                    self.set(key, value, context)
                    return value
            elif context is None:
                return self.cache[key]['value']
            else:
                return self.cache[context][key]['value']

import os
from datetime import datetime, timedelta
from json import JSONDecodeError, dump as json_dump, load as json_load
from threading import Lock
from typing import Callable, Union, Dict, Any, List


class Cache:
    """This class provides a simple cache with "expiry-on-retrieval"""

    current_cache = None  # type: Cache
    _global_context = '_'

    def __init__(self, file: str = None, notimeout=False):
        self.file = file if file is not None else os.path.join(os.getcwd(), '.cache')
        self.notimeout = notimeout
        self.cache = None
        self.lock = Lock()
        self._last_save = None

    def _save(self):
        with self.lock:
            print('Saving cache...')
            os.makedirs(os.path.dirname(self.file), exist_ok=True)
            json_dump(self.cache, open(self.file, 'w'))
            print('Cache saved.')

    def _maybe_save(self):
        # automatically save every 2 minutes
        if (datetime.now() - self._last_save) > timedelta(minutes=2):
            self._save()

    def __enter__(self):
        print('Opening cache...')
        with self.lock:
            self.__class__.current_cache = self
            if os.path.exists(self.file):
                try:
                    self.cache = json_load(open(self.file, 'r'))
                except JSONDecodeError:
                    self.cache = dict()
            else:
                self.cache = dict()
            self._last_save = datetime.now()
        print('Cache loaded.')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Closing cache...')
        self._save()
        print('Cache closed.')

    def remove(self, key, context):
        if context is None:
            self.remove(key, self._global_context)
        else:
            with self.lock:
                del self.cache[context][key]

        self._maybe_save()

    def _set(self, key: str, value: Union[str, int, float, Dict[str, Any]], context: str = None):
        if context is None:
            self._set(key, value, self._global_context)
        else:
            if context not in self.cache:
                self.cache[context] = dict()
            self.cache[context][key] = dict(value=value, time=datetime.now().timestamp())

        self._maybe_save()

    def set(self, key: str, value: Union[str, int, float, List[Any], Dict[str, Any]], context: str = None):
        """Insert or update a value"""

        with self.lock:
            self._set(key, value, context)

    def _has(self, key: str, maxage: timedelta, context: str = None) -> bool:
        if context is None:
            return self._has(key, maxage, self._global_context)
        else:
            if context not in self.cache or key not in self.cache[context]:
                return False
            time = self.cache[context][key]['time']
        return (datetime.now() - maxage) < datetime.fromtimestamp(time) or self.notimeout

    def has(self, key: str, maxage: timedelta, context: str = None) -> bool:
        """Check if we have a not-yet-expired value"""

        with self.lock:
            return self._has(key, maxage, context)

    def get(self, key: str, maxage: timedelta, context: str = None,
            func: Callable[[], Union[str, int, float, List[Any], Dict[str, Any]]] = None,
            locked_getter=True):
        """Retrieve, if possible, a value. Optionally compute and set it if not available"""

        with self.lock:
            if not self._has(key, maxage, context):
                if func is None:
                    return None
                else:
                    try:
                        if not locked_getter:
                            self.lock.release()
                        value = func()

                        if not isinstance(value, str) and not isinstance(value, int) and not isinstance(value, float) and not isinstance(value, list) and not isinstance(value, dict):
                            raise TypeError('Invalid type')

                        self._set(key, value, context)
                        return value
                    finally:
                        if not locked_getter:
                            self.lock.acquire()
            elif context is None:
                return self.cache[self._global_context][key]['value']
            else:
                return self.cache[context][key]['value']

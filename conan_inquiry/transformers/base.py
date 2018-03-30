import abc
import logging
import threading
from inspect import isclass

import requests
from cachecontrol import CacheControl
from dotmap import DotMap

from conan_inquiry.util.cache import Cache
from conan_inquiry.util.github import get_github_client


class BaseTransformer:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def _set_unless_exists(cls, obj, key, value):
        if key not in obj or obj[key] is None or obj[key] == '':
            obj[key] = value

    @abc.abstractmethod
    def transform(self, package: DotMap) -> DotMap:
        return package

    @property
    def cache(self):
        return Cache.current_cache


class TransformerChain(BaseTransformer):
    progress_bar_index = 0

    def __init__(self, transformers):
        super().__init__()
        # construct transformers who are given as classes
        self.transformers = [t() if isclass(t) else t for t in transformers]

    def transform(self, package):
        self.logger.info('Starting transform of "%s" in thread %s', package.id,
                         threading.current_thread().getName())
        self.progress_bar_index += 1
        # TODO: nested tqdm progress bars here
        for transformer in self.transformers:
            # tqdm(self.transformers, postfix=dict(pkg=package.id), position=self.progress_bar_index):
            transformer.logger.info('Transforming "%s"', package.id)
            package = transformer.transform(package)
        self.progress_bar_index -= 1
        self.logger.info('"%s" done', package.id)
        return package


class BaseHTTPTransformer(BaseTransformer):
    def __init__(self):
        super().__init__()
        self.http = CacheControl(requests.session())


class BaseGithubTransformer(BaseHTTPTransformer):
    def __init__(self):
        super().__init__()
        self.github = get_github_client(3)
        self.github_graph = get_github_client(4)

    def _set_repo(self, name):
        self.repo = self.github.get_repo(name)

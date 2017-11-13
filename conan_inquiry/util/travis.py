from datetime import timedelta

import requests

from conan_inquiry.util.cache import Cache


def repo_has_travis(github_id, http=None):
    if http is None:
        http = requests.session()
    res = Cache.current_cache.get(github_id, timedelta(days=1), 'github_travis',
                                  lambda: http.get('https://api.travis-ci.org/repos/' + github_id,
                                                   headers={'Accept': 'application/json'}).json())
    return 'last_build_id' in res and res['last_build_id'] is not None

"""Utility functions related to the Bintray API"""

import os
from datetime import timedelta
from json import JSONDecodeError

from requests import Session
from requests.auth import HTTPBasicAuth

from conan_inquiry.util.cache import Cache
from conan_inquiry.util.general import AtomicCounter


class BintrayRateLimitExceeded(Exception):
    def __init__(self, *args):
        super().__init__('Bintray rate limit exceeded', *args)


class Bintray:
    """Simple Bintray API client"""

    _rate_exceeded = False
    _rate_used = AtomicCounter(0)

    def __init__(self):
        self.auth = HTTPBasicAuth(os.getenv('BINTRAY_USERNAME'), os.getenv('BINTRAY_API_KEY'))
        if not self.auth.username or not self.auth.password:
            raise KeyError('Missing BINTRAY_USERNAME or BINTRAY_API_KEY environment variable')
        self.http = Session()
        self.rate = dict(limit=None, remaining=None)

    @property
    def rate_used(self):
        return self._rate_used.value

    def _get(self, path):
        if self._rate_exceeded:
            raise BintrayRateLimitExceeded()

        response = self.http.get('https://api.bintray.com/api/v1' + path, auth=self.auth)
        if 'x-ratelimit-limit' in response.headers:
            self.rate['limit'] = response.headers['x-ratelimit-limit']
            self.rate['remaining'] = response.headers['x-ratelimit-remaining']

        if response.status_code == 403 and 'exceeded your API call limit' in response.text:
            self._rate_exceeded = True
            print('Bintray exceeded {}/{} in {}'.format(self.rate['remaining'], self.rate['limit'], path))
            print(response.headers)
            raise BintrayRateLimitExceeded()

        self._rate_used.increment()

        if response.status_code == 404 or ('message' in response.json() and 'was not found' in response.json()['message']):
            raise FileNotFoundError(path)

        try:
            return response.status_code, response.json(), dict(response.headers)
        except JSONDecodeError as e:
            return ValueError('Unable to parse \'{}\' from {} as JSON: {}'.format(response.text, path, str(e)))

    def get(self, path, maxage=timedelta(days=28)):
        """Issue a GET request to the Bintray API and return the parsed reponse"""
        res = Cache.current_cache.get(path, maxage, 'bintray',
                                      lambda: self._get(path),
                                      locked_getter=False)
        if res[0] == 404 or ('message' in res[1] and 'was not found' in res[1]['message']):
            raise FileNotFoundError()
        return res[1]

    def _get_all(self, path):
        current_start = 0
        result = list()
        while True:
            code, json, headers = self._get(path + '?start_pos=' + str(current_start))
            if 'X-RangeLimit-Total' not in headers:
                return json

            result += json
            total = int(headers['X-RangeLimit-Total'])
            endpos = int(headers['X-RangeLimit-EndPos'])
            if endpos == total-1:
                break
            else:
                current_start = endpos + 1
        return result

    def get_all(self, path, maxage=timedelta(days=2)):
        return Cache.current_cache.get(path, maxage, 'bintray:getall',
                                       lambda: self._get_all(path))

    def download_url(self, subjectrepo, path):
        """Construct a Bintray download URL"""
        return 'https://dl.bintray.com/' + subjectrepo + '/' + path

    def load_licenses(self):
        """Retrieve the list of known licenses"""
        return self.get('/licenses/oss_licenses', maxage=timedelta(days=7))

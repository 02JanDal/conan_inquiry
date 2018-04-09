"""Utility functions related to Github"""
import hashlib
import json
import os

import sys
from datetime import timedelta

from github import Github
from github.Requester import Requester
from graphqlclient import GraphQLClient
from conan_inquiry.util.cache import Cache


class CachingRequester(Requester):
    def __init__(self, wrapped: Requester):
        #  login_or_token, password, base_url, timeout, client_id, client_secret, user_agent, per_page, api_preview
        super(CachingRequester, self).__init__(
            None,
            None,
            wrapped._Requester__base_url,
            wrapped._Requester__timeout,
            wrapped._Requester__clientId,
            wrapped._Requester__clientSecret,
            wrapped._Requester__userAgent,
            wrapped.per_page,
            wrapped._Requester__apiPreview
        )

    def requestJson(self, verb, url, parameters=None, headers=None, input=None, cnx=None):
        if Cache.current_cache is None:
            return super(CachingRequester, self).requestJson(verb, url, parameters, headers, input, cnx)
        
        rawkey = verb + url + json.dumps(parameters or dict()) + str(headers or dict()) + (input or '') + (cnx or '')
        key = hashlib.md5(rawkey.encode('utf-8')).hexdigest()

        requester = self
        def getter():
            print(url)
            return super(CachingRequester, requester).requestJson(verb, url, parameters, headers, input, cnx)

        res = Cache.current_cache.get(key, timedelta(days=7), 'github_raw', getter, locked_getter=False)
        return res[0], res[1], res[2]


def get_github_client(version):
    """
    Create a Github client for the given Github API version using credentials provided as
    environment variables
    """

    if version == 3:
        token = os.getenv('GITHUB_TOKEN')
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        if token is None or token == '':
            raise Exception('You need to set GITHUB_TOKEN using environment variables')
        if client_id is None or client_id == '':
            raise Exception('You need to set GITHUB_CLIENT_ID using environment variables')
        if client_secret is None or client_secret == '':
            raise Exception('You need to set GITHUB_CLIENT_SECRET using environment variables')

        gh = Github(login_or_token=token, client_id=client_id, client_secret=client_secret, per_page=100)
        #gh._Github__requester = CachingRequester(gh._Github__requester)
        return gh
    elif version == 4:
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token is None or github_token == '':
            raise Exception('You need to set GITHUB_TOKEN using environment variables')

        graph = GraphQLClient('https://api.github.com/graphql')
        graph.inject_token(github_token)
        return graph
    else:
        raise ValueError('Invalid API version {}, choose between 3 and 4'.format(version))

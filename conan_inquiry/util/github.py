"""Utility functions related to Github"""

import os

from github import Github
from graphqlclient import GraphQLClient


def get_github_client(version):
    """
    Create a Github client for the given Github API version using credentials provided as
    environment variables
    """

    if version == 3:
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        if client_id is None or client_id == '':
            raise Exception('You need to set GITHUB_CLIENT_ID using environment variables')
        if client_secret is None or client_secret == '':
            raise Exception('You need to set GITHUB_CLIENT_SECRET using environment variables')

        return Github(client_id=client_id, client_secret=client_secret)
    elif version == 4:
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token is None or github_token == '':
            raise Exception('You need to set GITHUB_TOKEN using environment variables')

        graph = GraphQLClient('https://api.github.com/graphql')
        graph.inject_token(github_token)
        return graph
    else:
        raise ValueError('Invalid API version {}, choose between 3 and 4'.format(version))

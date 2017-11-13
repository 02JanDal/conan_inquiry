import datetime
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import yaml
import os

from dotmap import DotMap
from github import RateLimitExceededException
from tqdm import tqdm

from conan_inquiry.transformers.base import TransformerChain
from conan_inquiry.transformers.bintray import BintrayTransformer
from conan_inquiry.transformers.boost import BoostTransformer
from conan_inquiry.transformers.github import GithubTransformer
from conan_inquiry.transformers.gitlab import GitLabTransformer
from conan_inquiry.transformers.simple import (LicenseDetectorTransformer, AuthorCombinerTransformer,
                                               ShortDescriptionTransformer, KeywordDuplicateEliminator, ReadmeFetcher,
                                               RemoveTemporariesTransformer)
from conan_inquiry.util.bintray import BintrayRateLimitExceeded
from conan_inquiry.util.cache import Cache
from conan_inquiry.util.github import get_github_client


def transform_package(file):
    data = yaml.load(open(file, 'r'))
    if data is None:
        print(file)
    data['id'] = os.path.basename(os.path.splitext(file)[0]).replace('.', '_')
    if 'exclude' in data and data['exclude']:
        return None

    # TODO: share transformer chains in the same thread
    transformers = TransformerChain([
        BoostTransformer,
        BintrayTransformer,
        GithubTransformer,
        GitLabTransformer,
        LicenseDetectorTransformer,
        AuthorCombinerTransformer,
        ShortDescriptionTransformer,
        KeywordDuplicateEliminator,
        ReadmeFetcher,
        RemoveTemporariesTransformer
    ])
    try:
        return transformers.transform(DotMap(data)).toDict()
    except BintrayRateLimitExceeded or RateLimitExceededException:
        raise
    except Exception as e:
        return data['id'], e


class Generator:
    def __init__(self, packages_dir):
        self.packages_dir = packages_dir
        ShortDescriptionTransformer.prepare()

    def transform_packages(self):
        github = get_github_client(3)
        rate_before = github.get_rate_limit().rate
        try:
            with Cache(os.getenv('CACHE_FILE')):
                packages = [os.path.join(self.packages_dir, f)
                            for f in os.listdir(self.packages_dir)
                            if os.path.isfile(os.path.join(self.packages_dir, f))]
                with ThreadPoolExecutor(len(packages)) as executor:
                    futures = [executor.submit(transform_package, package) for package in packages]
                    for f in tqdm(as_completed(futures),
                                  total=len(futures), unit='package', unit_scale=True,
                                  leave=True, position=0, ncols=80):
                        pass
                    results = [f.result() for f in futures]
                    errors = [r for r in results if isinstance(r, tuple)]
                    for error in errors:
                        exc = error[1]
                        print('Error in {}: {}\n{}'.format(
                            error[0], str(exc),
                            ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))))
                    if len(errors) > 0:
                        sys.exit(1)

                    data = json.dumps([r for r in results if r is not None], indent=2)
                    with open('packages.json', 'w') as file:
                        file.write(data)
                    with open('packages.js', 'w') as file:
                        file.write('var packages_data = \n')
                        file.write(data)
                        file.write(';')
        finally:
            rate = github.get_rate_limit().rate
            print('Github rate limiting:\n\tRemaining: {}/{}\n\tUsed this call: {}\n\tResets: {}'.format(
                rate.remaining, rate.limit, rate_before.remaining - rate.remaining,
                (rate.reset + datetime.timedelta(hours=1)) - datetime.datetime.now()))

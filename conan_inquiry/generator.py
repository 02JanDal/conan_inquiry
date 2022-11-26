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
                                               RemoveTemporariesTransformer, AddEmptyTransformer, CategoriesTransformer,
                                               OfficiallityTransformer)
from conan_inquiry.util.bintray import BintrayRateLimitExceeded, Bintray
from conan_inquiry.util.cache import Cache
from conan_inquiry.util.github import get_github_client


def transform_package(file):
    # Get pre-transform data
    data = yaml.load(open(file, 'r'))
    if data is None:
        print(file)
    data['id'] = os.path.basename(os.path.splitext(file)[0]).replace('.', '_')
    if 'exclude' in data and data['exclude'] or 'see' in data:
        return None

    # TODO: share transformer chains in the same thread
    # TODO: bitbucket transformer
    # TODO: sourceforge transformer
    # TODO: generic gitlab transformer
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
        CategoriesTransformer,
        OfficiallityTransformer,
        RemoveTemporariesTransformer,
        AddEmptyTransformer
    ])
    try:
        return transformers.transform(DotMap(data)).toDict()
    except BintrayRateLimitExceeded or RateLimitExceededException:
        tqdm.write('Rate limit reached for {}'.format(data['id']))
        raise
    except Exception as e:
        tqdm.write('Exception for {}'.format(data['id']))
        return data['id'], e


class Generator:
    def __init__(self, packages_dir):
        self.packages_dir = packages_dir
        ShortDescriptionTransformer.prepare()

    def transform_packages(self, development=False):
        """"""

        github = get_github_client(3)
        # Used to calculate the resources used
        rate_before = github.get_rate_limit().rate
        try:
            with Cache(os.getenv('CACHE_FILE'), notimeout=development):
                # Collect package files
                packages = [os.path.join(self.packages_dir, f)
                            for f in os.listdir(self.packages_dir)
                            if os.path.isfile(os.path.join(self.packages_dir, f))]

                if 'PARTITION' in os.environ:
                    partition = int(os.environ.get('PARTITION'))
                    packages = packages[partition*50:(partition+1)*50]

                with ThreadPoolExecutor(min(len(packages), 50)) as executor:
                    # Generate for all packages
                    futures = [executor.submit(transform_package, package) for package in packages]
                    for _ in tqdm(as_completed(futures),
                                  total=len(futures), unit='package', unit_scale=True,
                                  leave=True, position=0, ncols=80):
                        pass

                    # Get results from futures and filter/print errors
                    results = [f.result() for f in futures]
                    errors = [r for r in results if isinstance(r, tuple)]
                    for error in errors:
                        exc = error[1]
                        print('Error in {}: {}\n{}'.format(
                            error[0], str(exc),
                            ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))))
                    if len(errors) > 0 and not development:
                        print('Errors in {} packages have prevented writing of packages.js'.format(len(errors)))
                        sys.exit(1)
                    elif len(errors) > 0 and development:
                        print('Errors in {} packages prevented them from being generated'.format(len(errors)))

                    # Write new package files
                    data = json.dumps([r for r in results if r is not None], indent=2)
                    with open('packages.json', 'w') as file:
                        file.write(data)
                    with open('packages.js', 'w') as file:
                        file.write('var packages_data = \n')
                        file.write(data)
                        file.write(';')

                    print('All generation steps succeeded and package data written')
        finally:
            rate = github.get_rate_limit().rate
            print('Github rate limiting:\n\tRemaining: {}/{}\n\tUsed this call: {}\n\tResets: {}'.format(
                rate.remaining, rate.limit, rate_before.remaining - rate.remaining,
                (rate.reset + datetime.timedelta(hours=1)) - datetime.datetime.now()))

            bt = Bintray()
            print('Bintray rate limiting:\n\tUsed this call: {}'.format(bt.rate_used))

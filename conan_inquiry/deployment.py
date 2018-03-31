from datetime import datetime
from tempfile import TemporaryDirectory

import os
import subprocess
import shutil
import hashlib


def deploy():
    with TemporaryDirectory() as dir:
        print('* Deploying with tempdir:', dir)

        def git(subcmd, *args, **kwargs):
            kwargs.setdefault('cwd', os.path.join(dir, 'conan_inquiry'))

            print('* Running: git', subcmd, *args)
            retcode = subprocess.call(['git', subcmd] + list(args), **kwargs)
            if retcode != 0:
                raise ChildProcessError('Unable to run the command')

        git('clone', os.getenv('GITHUB_REPO', 'git@github.com:02JanDal/conan_inquiry.git'),
            '--branch', 'gh-pages',
            '--single-branch',
            cwd=dir)

        webpath = os.path.join(os.path.dirname(__file__), 'data/web')
        for file in ['packages.json', 'packages.js', webpath + '/index.html', webpath + '/script.js']:
            shutil.copy(file, os.path.join(dir, 'conan_inquiry'))
            git('add', os.path.join(dir, 'conan_inquiry', os.path.basename(file)))

        index_html_name = os.path.join(dir, 'conan_inquiry', 'index.html')
        with open(index_html_name, 'rt') as file:
            index_html_data = file.read()
        index_html_data = index_html_data.replace('CACHE_BUSTER',
                                                  hashlib.md5(datetime.now().isoformat().encode('utf-8')).hexdigest())
        print(index_html_data)
        with open(index_html_name, 'wt') as file:
            file.write(index_html_data)
        git('add', index_html_name)

        git('commit', '--amend', '-m', '"Automatic deployment"')
        git('push', '-f', 'origin', 'gh-pages')
        print('* Deployment successful!')
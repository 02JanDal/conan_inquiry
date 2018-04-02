from datetime import datetime
from tempfile import TemporaryDirectory

import os
import subprocess
import shutil
import hashlib

from conan_inquiry.web.file_retrieval import WebFiles


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

        files = WebFiles()

        for file in files.names():
            with open(os.path.join(dir, 'conan_inquiry', file), 'wt') as f:
                f.write(files.get_file(file, debug=False))
            git('add', os.path.join(dir, 'conan_inquiry', file))

        git('commit', '--amend', '-m', '"Automatic deployment"')
        git('push', '-f', 'origin', 'gh-pages')
        print('* Deployment successful!')
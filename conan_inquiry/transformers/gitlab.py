import os
from datetime import timedelta

from gitlab import Gitlab

from conan_inquiry.transformers.base import BaseTransformer


class GitLabTransformer(BaseTransformer):
    def transform(self, package):
        if 'gitlab' in package.urls:
            clean = package.urls.gitlab.replace('https://', '').replace('http://', '').split('/')
            if len(clean) == 2:
                host = 'gitlab.com'
                project = '/'.join(clean)
            else:
                host = clean[0]
                project = '/'.join(clean[1:3])
            env_name = 'GITLAB_' + host.replace('.', '_').replace('-', '_').upper() + '_TOKEN'
            token = os.getenv(env_name)
            if token is None or '' == token:
                print('You need to set ' + env_name + ' using environment variables')
                return package

            def get_gitlab_project(host, project):
                gitlab = Gitlab('https://' + host, token, api_version=4)
                repo = gitlab.projects.get(project, statistics=True)
                return dict(
                    git=repo.http_url_to_repo,
                    code=repo.web_url,
                    description=repo.description,
                    logo=repo.avatar_url,
                    forks=repo.forks_count,
                    stars=repo.star_count,
                    commits=repo.statistics['commit_count'],
                    issues_enabled=repo.issues_enabled,
                    issues=repo.open_issues_count if repo.issues_enabled else None,
                    mrs_enabled=repo.merge_requests_enabled,
                    mrs=None,
                    name=repo.name
                )

            proj = self.cache.get(host + '#' + project,
                                  timedelta(days=7), 'gitlab',
                                  lambda: get_gitlab_project(host,
                                                             project))

            self._set_unless_exists(package.urls, 'git', proj['git'])
            self._set_unless_exists(package.urls, 'code', proj['code'])
            self._set_unless_exists(package, 'description', proj['description'])
            self._set_unless_exists(package, 'logo', proj['logo'])
            self._set_unless_exists(package.stats, 'gitlab_forks', proj['forks'])
            self._set_unless_exists(package.stats, 'gitlab_stars', proj['stars'])
            self._set_unless_exists(package.stats, 'commits', proj['commits'])
            if proj['issues_enabled']:
                self._set_unless_exists(package.stats, 'gitlab_issues', proj['issues'])
                self._set_unless_exists(package.urls, 'issues', proj['code'] + '/issues')
            if proj['mrs_enabled']:
                pass  # self._set_unless_exists(package.stats, 'gitlab_mrs', repo)
            self._set_unless_exists(package, 'name', proj['name'])
        return package

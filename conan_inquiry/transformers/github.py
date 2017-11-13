import json
from base64 import b64decode
from datetime import timedelta

import github
import os

from dotmap import DotMap
from github import GithubException

from conan_inquiry.transformers.base import BaseGithubTransformer
from conan_inquiry.util.general import render_readme
from conan_inquiry.util.travis import repo_has_travis


class GithubTransformer(BaseGithubTransformer):
    """
    Populates empty urls based on the Github url, if given
    """

    def transform(self, package):
        if 'github' in package.urls:
            github_id = package.urls.github
            try:
                self._set_repo(github_id)
                graph_request = '''
                    query Repo($owner:String!, $name:String!) {
                      repo: repository(owner: $owner, name: $name) {
                        owner {
                          login
                          ... on Organization {
                            name
                            orgEmail: email
                            websiteUrl
                          }
                          ... on User {
                            name
                            userEmail: email
                            websiteUrl
                          }
                        }
                        tree: object(expression: "HEAD:") {
                          ... on Tree {
                            entries {
                              name
                            }
                          }
                        }
                        repositoryTopics(first: 20) {
                          totalCount
                          nodes {
                            topic {
                              name
                            }
                          }
                        }
                        forks {
                          totalCount
                        }
                        description
                        hasIssuesEnabled
                        hasWikiEnabled
                        homepageUrl
                        url
                        openIssues: issues(states: OPEN) {
                          totalCount
                        }
                        closedIssues: issues(states: CLOSED) {
                          totalCount
                        }
                        openPRs: pullRequests(states: OPEN) {
                          totalCount
                        }
                        closedPRs: pullRequests(states: CLOSED) {
                          totalCount
                        }
                        pushedAt
                        stargazers {
                          totalCount
                        }
                        watchers {
                          totalCount
                        }
                      }
                      rateLimit {
                        cost
                        remaining
                      }
                    }
                '''
                graph_data = self.cache.get(github_id, timedelta(hours=6), 'github_graph',
                                            lambda: self.github_graph.execute(
                                                graph_request,
                                                dict(owner=self.repo.owner.login,
                                                     name=self.repo.name)))
                graph = json.loads(graph_data)['data']
            except GithubException:
                return package

            if graph['repo']['description'] != package.name:
                self._set_unless_exists(package, 'description', graph['repo']['description'])

            self._set_unless_exists(package.urls, 'website', graph['repo']['homepageUrl'])
            self._set_unless_exists(package.urls, 'code', graph['repo']['url'])
            if graph['repo']['hasIssuesEnabled']:
                self._set_unless_exists(package.urls, 'issues', graph['repo']['url'] + '/issues')
            if graph['repo']['hasWikiEnabled']:
                # TODO: check if there is content in the wiki
                self._set_unless_exists(package.urls, 'wiki', graph['repo']['url'] + '/wiki')

            if repo_has_travis(github_id, self.http):
                self._set_unless_exists(package.urls, 'travis',
                                        'https://travis-ci.org/' + github_id)
            self._set_unless_exists(package.urls, 'git', self.repo.clone_url)

            try:
                def get_readme(repo, github):
                    readme = repo.get_readme()
                    rendered = render_readme(readme.path, readme.decoded_content.decode('utf-8'),
                                             graph['repo']['url'],
                                             lambda raw: github.render_markdown(raw, repo).decode('utf-8'))
                    return dict(url=readme.html_url, content=rendered)

                readme = self.cache.get(github_id, timedelta(hours=12), 'github_readme',
                                        lambda: get_readme(self.repo, self.github))
                self._set_unless_exists(package.urls, 'readme', readme['url'])
                self._set_unless_exists(package.files.readme, 'url', readme['url'])
                self._set_unless_exists(package.files.readme, 'content', readme['content'])
            except github.UnknownObjectException:
                pass

            for entry in graph['repo']['tree']['entries']:
                if os.path.basename(entry['name']).lower() == 'license':
                    file = self.repo.get_file_contents(entry['name'])
                    self._set_unless_exists(package, 'license', file.html_url)
                    self._set_unless_exists(package, '_license_data', str(b64decode(file.content)))
                    break

            if 'authors' not in package:
                owner = graph['repo']['owner']
                if 'userEmail' in owner:
                    # private repo
                    name = owner['name'] if owner['name'] is not None else owner['login']
                    author = DotMap(name=name,
                                    github=owner['login'])
                    email = owner['userEmail']
                    website = owner['websiteUrl']
                    if email is not None:
                        author.email = email
                    if website is not None:
                        author.website = website
                    package.authors = [author]
                else:
                    # organization repo
                    name = owner['name'] if owner['name'] is not None else owner['login']
                    author = DotMap(name=name,
                                    github=owner['login'])
                    email = owner['orgEmail']
                    website = owner['websiteUrl']
                    if email is not None:
                        author.email = email
                    if website is not None:
                        author.website = website
                    package.authors = [author]

            self._set_unless_exists(package.stats, 'github_prs', graph['repo']['openPRs']['totalCount'])
            self._set_unless_exists(package.stats, 'github_issues', graph['repo']['openIssues']['totalCount'])
            self._set_unless_exists(package.stats, 'github_stars', graph['repo']['stargazers']['totalCount'])
            self._set_unless_exists(package.stats, 'github_watchers', graph['repo']['watchers']['totalCount'])
            self._set_unless_exists(package.stats, 'github_forks', graph['repo']['forks']['totalCount'])
            # TODO: the number of commits does not seem to be correct and sometimes fetching doesn't work at all
            contributors = self.repo.get_stats_contributors()
            if contributors is not None:
                self._set_unless_exists(package.stats, 'github_commits',
                                        sum([c.total for c in contributors]))
            commits = self.repo.get_commits()
            self._set_unless_exists(package.stats, 'github_latest_commit',
                                    commits[0].commit.committer.date.isoformat())

            if 'keywords' not in package:
                package.keywords = []
            package.keywords.extend([r['topic']['name'] for r in graph['repo']['repositoryTopics']['nodes']])
        for recipie in package.recipies:
            if 'github' in recipie.urls:
                self._set_unless_exists(recipie.urls, 'website', 'https://github.com/' + recipie.urls.github)
                self._set_unless_exists(recipie.urls, 'issues', 'https://github.com/' + recipie.urls.github + '/issues')
        return package

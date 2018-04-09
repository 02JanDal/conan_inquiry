import json
import os

from jsonschema import Draft4Validator

schema = dict(
    type='array',
    items=dict(
        type='object',
        properties=dict(
            id=dict(type='string', minLength=1),
            name=dict(type='string', minLength=1),
            description=dict(type='string', minLength=5),
            short_description=dict(type='string', minLength=5),
            urls=dict(
                type='object',
                properties={k: dict(type='string', format='uri')
                            for k in ['website', 'issues', 'wiki', 'code', 'git', 'docs']}
            ),
            author=dict(type='string'),
            authors=dict(
                type='array',
                minLength=1,
                items=dict(
                    type='object',
                    properties=dict(
                        name=dict(type='string'),
                        website=dict(type='string', format='uri'),
                        github=dict(type='string', pattern='^[A-Za-z0-9_-]+$'),
                        email=dict(type='string', format='email')
                    ),
                    required=['name']
                )
            ),
            recipies=dict(
                type='array',
                minLength=1,
                items=dict(
                    type='object',
                    properties=dict(
                        package=dict(type='string'),
                        remote=dict(type='string', format='uri'),
                        user=dict(type='string'),
                        repo=dict(
                            type='object',
                            properties=dict(
                                bintray=dict(type='string')
                            ),
                            required=['bintray']
                        ),
                        urls=dict(
                            type='object',
                            properties={k: dict(type='string', format='uri')
                                        for k in ['website', 'issues', 'code', 'git', 'docs']}
                        ),
                        versions=dict(
                            type='array',
                            minLength=1,
                            items=dict(
                                type='object',
                                properties=dict(
                                    name=dict(type='string'),
                                    channel=dict(type='string')
                                ),
                                required=['name', 'channel']
                            )
                        )
                    )
                )
            ),
            files=dict(
                type='object',
                patternProperties={
                    '^.*$': dict(
                        type='object',
                        properties=dict(
                            content=dict(type='string'),
                            url=dict(type='string', format='uri')
                        ),
                        required=['content', 'url']
                    )
                },
                additionalProperties=False
            ),
            keywords=dict(
                type='array',
                items=dict(type='string'),
                uniqueItems=True
            ),
            categories=dict(
                type='array',
                items=dict(type='string'),
                uniqueItems=True
            ),
            licenses=dict(
                type='array',
                items=dict(
                    type='object',
                    properties=dict(
                        url=dict(type='string'),
                        name=dict(type='string'),
                        longname=dict(type='string')
                    ),
                    required=['url', 'name']
                )
            )
        ),
        required=['id', 'name', 'description', 'short_description', 'author', 'authors', 'categories', 'keywords']
    )
)


def validate_packages(dir):
    with open(os.path.join(dir, 'packages.json')) as f:
        data = json.load(f)

    def is_valid(key: str, dict: dict):
        return key in dict and dict[key] is not None and dict[key] != ''

    packages_missing_authors = [p['id'] for p in data if len(p['authors']) == 0]
    packages_missing_website = [p['id'] for p in data if 'urls' not in p or not is_valid('website', p['urls'])]
    packages_missing_issues = [p['id'] for p in data if 'urls' not in p or not is_valid('issues', p['urls'])]
    packages_missing_code = [p['id'] for p in data if 'urls' not in p or not is_valid('code', p['urls'])]
    packages_missing_docs = [p['id'] for p in data if 'urls' not in p or not is_valid('docs', p['urls'])]
    packages_missing_desc = [p['id'] for p in data if not is_valid('description', p)]
    packages_missing_sdesc = [p['id'] for p in data if not is_valid('short_description', p)]

    packages_missing = set()
    packages_missing.update(packages_missing_authors)
    packages_missing.update(packages_missing_website)
    packages_missing.update(packages_missing_issues)
    packages_missing.update(packages_missing_code)
    packages_missing.update(packages_missing_docs)
    packages_missing.update(packages_missing_desc)
    packages_missing.update(packages_missing_sdesc)
    packages_missing = [p for p in packages_missing]
    packages_missing.sort()
    if len(packages_missing) > 0:
        for pkg in packages_missing:
            missing = []
            if pkg in packages_missing_authors:
                missing.append('authors')
            if pkg in packages_missing_website:
                missing.append('website')
            if pkg in packages_missing_issues:
                missing.append('issues')
            if pkg in packages_missing_code:
                missing.append('code')
            if pkg in packages_missing_docs:
                missing.append('docs')
            if pkg in packages_missing_desc:
                missing.append('description')
            if pkg in packages_missing_sdesc:
                missing.append('short_description')
            print('missing in ' + pkg + ': ' + ', '.join(missing))

    Draft4Validator.check_schema(schema)
    for r in Draft4Validator(schema).iter_errors(data):
        print('--- Error in {}\n{}'.format(data[r.path[0]]['id'], str(r)))

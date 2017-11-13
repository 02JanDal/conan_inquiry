import re
from docutils.core import publish_parts as rst_publish_parts


def render_readme(path, raw_str, absolute_url, github_renderer=None):
    link_re = re.compile(r'(<a.*? href=")([^"]*)(")')

    if path.lower().endswith('.md'):
        if github_renderer:
            rendered = github_renderer(raw_str)
        else:
            raise NotImplementedError('add non-github markdown renderer')
    elif path.lower().endswith('.rst'):
        rendered = rst_publish_parts(raw_str, writer_name='html')['html_body']
    else:
        rendered = raw_str
    # a very naive regex-based approach to make relative urls absolute
    rendered = link_re.sub(
        lambda a: a.group(1) + (a.group(2) if '/' in a.group(2) else absolute_url + '/' + a.group(2)) + a.group(3),
        rendered
    )
    return rendered

import re
from datetime import timedelta

from bs4 import BeautifulSoup
from dotmap import DotMap

from conan_inquiry.transformers.base import BaseHTTPTransformer


class BoostTransformer(BaseHTTPTransformer):
    author_re = re.compile(r'<h3 class="author">(.*?)</h3>')
    first_ps_re = re.compile(
        r'<div class="chapter">.*<div class="section">.*<div class="titlepage">.*?(<p>.*?<\/p>)<[^p]+>')
    first_p_re = re.compile(r'<p>(.*?)</p>')
    blockquote_re = re.compile(r'<blockquote.*?</blockquote>')

    def __init__(self):
        super().__init__()
        authors_text = self.http.get(
            'https://raw.githubusercontent.com/boostorg/boost/master/libs/maintainers.txt').text
        self.authors = {line.split(' ')[0]: ' '.join(line.split(' ')[1:]).strip()
                        for line in authors_text.split('\n')
                        if not line.startswith('#') and line.strip() != ''}

    def transform(self, package):
        if package.id.startswith('boost_'):
            boost_id = package.id.replace('boost_', '')
            self._set_unless_exists(package.urls, 'issues',
                                    'http://www.boost.org/development/bugs.html')

            def http_get_json(url):
                res = self.http.get(url)
                return dict(
                    code=res.status_code,
                    json=res.json() if res.status_code == 200 else None
                )

            def http_get_text(url):
                res = self.http.get(url)
                return dict(
                    code=res.status_code,
                    text=res.text if res.status_code == 200 else None
                )

            metaurl = 'https://raw.githubusercontent.com/boostorg/' + boost_id + '/develop/meta/libraries.json'
            metares = self.cache.get(metaurl, timedelta(days=1), 'boost_docs',
                                     lambda: http_get_json(metaurl))
            if metares['code'] == 200:
                package.urls.github = 'boostorg/' + boost_id

                meta = metares['json']
                if isinstance(meta, list):
                    meta = meta[0]
                if 'keywords' not in package:
                    package.keywords = []
                package.keywords.extend([k.lower() for k in meta['category']])

                if 'authors' not in package:
                    package.authors = []
                if 'maintainers' in meta:
                    package.authors.extend([DotMap(name=a.split('<')[0].strip(),
                                                   email=a.split('<')[1].replace('>', '').replace(
                                                       ' -at- ', '@').strip())
                                            for a in meta['maintainers']])
                else:
                    package.authors.extend([DotMap(name=author)
                                            for author in meta['authors']])

            if boost_id in ['bimap', 'parameter', 'phoenix']:
                self._set_unless_exists(package, 'description', meta['description'])
            else:
                boost_url = package.urls.boost if 'boost' in package.urls else boost_id
                docurl = 'http://www.boost.org/doc/libs/release/libs/' + boost_url
                docres = self.cache.get(docurl, timedelta(days=1), 'boost_docs',
                                        lambda: http_get_text(docurl))
                if docres['code'] == 200:
                    self._set_unless_exists(package.urls, 'docs', docurl)

                    bs = BeautifulSoup(docres['text'], 'html.parser')
                    for tags in ['table', 'dl', 'script', 'style', 'blockquote', 'head']:
                        for tag in bs.find_all(tags):
                            tag.decompose()
                    for selector in ['#boost-common-heading-doc', '#boost-common-heading-doc-spacer',
                                     '.spirit-nav', '.toc', '#header', '#footer', '.titlepage',
                                     '.blockquote', 'blockquote', 'hr', '#boost-logo']:
                        for tag in bs.select(selector):
                            tag.decompose()

                    preamble = bs.find(id='preamble')
                    first_p = next((p for p in bs.find_all('p') if len(p.contents) > 0), None)
                    if preamble is not None:
                        self._set_unless_exists(package, 'description',
                                                self._clean_desc(preamble.find_all('p')))
                    elif first_p is not None:
                        ps = [first_p]
                        while first_p.next_sibling is not None and first_p.next_sibling.name == 'p':
                            ps.append(first_p.next_sibling)
                            first_p = first_p.next_sibling
                        self._set_unless_exists(package, 'description', self._clean_desc(ps))
        return package

    @classmethod
    def _clean_desc(cls, ps):
        for p in ps:
            for code in p.select('code.computeroutput'):
                code['class'].remove('computeroutput')
                for span in code.find_all('span'):
                    span.unwrap()
        if len(ps) == 1:
            desc = str(ps[0]).replace('<p>', '').replace('</p>', '')
        else:
            desc = ''.join(str(p) for p in ps)
        desc = re.sub(r'  +', ' ', desc.replace('\n', ' '))
        return desc.strip()

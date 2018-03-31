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

    listing = None

    def _listing(self):
        raw = self.http.get('https://www.boost.org/doc/libs/')
        bs = BeautifulSoup(raw.text, 'html.parser')
        dl = bs.dl
        list_of_libraries = []
        for dt in [dt for dt in dl.children if dt.name == 'dt']:
            name = dt.a.get_text()
            url = dt.a['href'].replace('/doc/libs/release/libs/', '')
            # remove some extra stuff in some URLs
            for search in ['/doc/index.html', '/dynamic_bitset.html', '/doc/interval.htm', '/utility.htm',
                           '/doc/boost-exception.html', '/config.htm', '/doc/html', '/doc/ios_state.html']:
                url = url.replace(search, '')
            dd = dt.next_sibling.next_sibling
            description = dd.p.get_text()
            list_of_libraries.append(dict(
                name=name,
                url=url.strip('/').replace('/', '_'),
                description=description
            ))
        return list_of_libraries

    def __init__(self):
        super().__init__()
        authors_text = self.http.get(
            'https://raw.githubusercontent.com/boostorg/boost/master/libs/maintainers.txt').text
        self.authors = {line.split(' ')[0]: ' '.join(line.split(' ')[1:]).strip()
                        for line in authors_text.split('\n')
                        if not line.startswith('#') and line.strip() != ''}

        if self.listing is None:
            self.listing = self.cache.get('boost_listing', maxage=timedelta(days=28),
                                          func=self._listing, locked_getter=True)

    def transform(self, package):
        if package.id.startswith('boost_'):
            boost_id = package.id.replace('boost_', '')
            self._set_unless_exists(package.urls, 'issues',
                                    'http://www.boost.org/development/bugs.html')

            listing = next((l for l in self.listing if l['url'] == boost_id), None)
            if listing is not None:
                self._set_unless_exists(package, 'name', 'Boost.' + listing['name'].replace(' ', ''))
                self._set_unless_exists(package, 'short_description', listing['description'])
            else:
                self._set_unless_exists(package, 'name',
                                        'Boost.' + ''.join([i.title() for i in boost_id.split('_')]))

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
                                     lambda: http_get_json(metaurl),
                                     locked_getter=False)
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
                                        lambda: http_get_text(docurl),
                                        locked_getter=False)
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

import hashlib
import os

import re
from datetime import datetime

from jsmin import jsmin


class WebFiles:
    replacement_html_re = re.compile(r'<import +href="([^"]+)"(/>|></import>)')
    replacement_js_re = re.compile(r'//import (\S+)')
    dir = os.path.join(os.path.dirname(__file__), 'files')

    def full_name(self, name):
        if self.is_constant(name):
            return os.path.join(os.path.dirname(__file__), '..', '..', 'build', name)
        return os.path.join(self.dir, name)

    def exists(self, name):
        return os.path.exists(self.full_name(name))

    def get_file(self, name: str, debug=False):
        if not self.exists(name):
            return None

        with open(self.full_name(name), 'r') as f:
            result = f.read()

        result = self.replacement_html_re.sub(lambda x: self.get_file(x.group(1)), result)
        result = self.replacement_js_re.sub(lambda x: self.get_file(x.group(1)), result)
        if not debug:
            result = result.replace('CACHE_BUSTER',
                                    hashlib.md5(datetime.now().isoformat().encode('utf-8')).hexdigest())

        if name.endswith('.js'):
            result = jsmin(result)

        return result

    def size(self, name):
        return os.path.getsize(self.full_name(name))

    def names(self):
        files = ['packages.js', 'packages.json']
        for entry in os.listdir(self.dir):
            full_name = os.path.join(self.dir, entry)
            if os.path.isfile(full_name) and not entry.startswith('_'):
                files.append(entry)
        return files

    def is_constant(self, name):
        return name == 'packages.js' or name == 'packages.json'

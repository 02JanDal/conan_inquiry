App.category = {};
App.category.$ = $('#categoryView');
App.category.link = function(part, noLink) {
    if (noLink) {
        return part.name;
    }
    return '<a href="' + App.router.generate('category', {name: part.id}) + '">' + part.name + '</a>';
};
App.category.readable = function(category, onlyLeaf, noLink) {
    var replacements = {
        'cpp': 'C++',
        'lowlevel': 'Low Level',
        'highlevel': 'High Level',
        'fileformat': 'File Format',
        'png': 'PNG',
        'jpeg': 'JPEG',
        'gif': 'GIF',
        'tiff': 'TIFF',
        'xml': 'XML',
        'json': 'JSON',
        'yaml': 'YAML',
        'msgpack': 'MessagePack',
        '3dmodel': '3D Model',
        'websockets': 'WebSockets',
        'http': 'HTTP',
        '3d': '3D',
        'opengl': 'OpenGL',
        'mqtt': 'MQTT',
        'pubsub': 'Pub/Sub',
        'sip': 'SIP',
        'dns': 'DNS',
        'zeromq': 'ZeroMQ',
        'io': 'IO',
        'i18n': 'i18n',
        'orm': 'ORM',
        'mysql': 'MySQL',
        'odbc': 'ODBC',
        'sqlite': 'SQLite',
        'zip': 'ZIP',
        'regexp': 'Regular Expressions',
        'rpc': 'RPC',
        'cli_parsing': 'CLI Parsing',
        'dsl': 'DSL',
        'ai': 'AI',
        'statemachine': 'State Machines',
        'datetime': 'Date/Time',
        'bindings_interoperability': 'Bindings/Interoperability',
        'signals_slots': 'Signals & Slots',
        'mq': 'Message Queue',
        'drm': 'DRM',
        'system_framework': 'System/Framework',
        'csv': 'CSV',
        'vr_ar': 'VR/AR',
        'postgresql': 'PostgreSQL'
    };

    var parts = category.split('.');
    parts = _.map(parts, function(part, index) {
        var id = category.split('.').splice(0, index+1).join('.');
        if (part in replacements) {
            return {id: id, name: replacements[part]};
        } else {
            return {id: id, name: part.split('_').map(function(s) { return s.toTitleCase(); }).join(' ')};
        }
    });

    if (category.startsWith('standard.')) {
        if (onlyLeaf) {
            if (parts.length === 2) {
                return this.link(parts[1], noLink);
            } else {
                return parts[1].name + this.link(parts[2], noLink);
            }
        } else {
            if (parts.length === 2) {
                return 'Standard: ' + this.link(parts[1]);
            } else {
                return 'Standard: ' + this.link(parts[1]) + this.link(parts[2]);
            }
        }
    } else if (category.startsWith('status.')) {
        parts[1].name = parts[1].name.substr(1).toTitleCase();
        if (onlyLeaf) {
            return this.link(parts[1], noLink);
        }
        return 'Status: ' + this.link(parts[1]);
    } else if (category.startsWith('environment.')) {
        if (onlyLeaf) {
            return this.link(parts[1], noLink);
        }
        return 'Environment: ' + this.link(parts[1]);
    } else if (category.startsWith('topic.')) {
        if (parts.length > 2) {
            var ret = parts[1].name + ': ';
            parts = _.map(parts.splice(2), function(p) { return this.link(p, noLink); }, this);
            if (onlyLeaf) {
                return parts[parts.length-1];
            }
            return ret + parts.join(' &gt; ');
        } else {
            return parts[1].name;
        }
    }
    return category.toTitleCase();
};
App.category.filter = function(categories) {
    return _.filter(categories, function(cat) {
        var subs = _.filter(categories, function(subcat) { return subcat.startsWith(cat + '.'); });
        return subs.length === 0;
    });
};
App.category.all = _.chain(packages_data).map(_.property('categories')).flatten().value();
App.category.allUnique = _.chain(App.category.all).uniq().sort().value();
App.category.counts = _.countBy(App.category.all, _.identity);
App.category.pkgCounts = _.chain(packages_data).map(_.property('categories')).map(App.category.filter).flatten().countBy(_.identity).value();
App.category.forCategory = function(subcat, includeSubs) {
    var pkgs = _.filter(packages_data, function(pkg) { return pkg.categories.includes(subcat); });
    if (!includeSubs) {
        pkgs = _.filter(pkgs, function (pkg) {
            // true if the subcat is an absolute leaf (no subcategories in this package)
            return !_.find(pkg.categories, function (cat) {
                return cat.startsWith(subcat + '.');
            });
        });
    }
    return pkgs;
};
App.category.sortStandards = function(categories) {
    return _.sortBy(categories, function(cat) { // order by year
        var parts = cat.split('.');
        var result = 0;
        if (parts[1] === 'c') {
            result = 10000;
        } else if (parts[1] === 'cpp') {
            result = 20000;
        }

        if (parts.length >= 3) {
            var shortYear = parseInt(cat.split('.')[2]);
            result += shortYear;
            result += shortYear > 70 ? 1900 : 2000;
        }

        return result;
    });
};
App.category.readableStandards = function(categories) {
    var standards = this.filter(categories);
    standards = _.filter(standards, function(cat) { return cat.startsWith('standard.'); });
    standards = this.sortStandards(standards);
    standards = _.map(standards, function(cat) {
        return cat.replace('standard.', '').replace('cpp', 'c++').replace('.', '').toTitleCase();
    }).join('/');

    return standards;
};

$('[data-menu-prefix]').each(function(index, menu) {
    var $menu = $(menu);
    var prefix = $menu.attr('data-menu-prefix');
    var categories = _.filter(App.category.allUnique, function(cat) {
        return cat.startsWith(prefix) && cat.split('.').length === prefix.split('.').length;
    });
    categories.sort();
    _.each(categories, function(cat) {
        $menu.append(App.templates.menuItem({
            name: App.category.readable(cat, true, true),
            href: App.router.generate('category', {name: cat}),
            count: App.category.counts[cat]
        }));
    });
});
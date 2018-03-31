$(function() {
    $('#numPackages').html(packages_data.length);
    var repos = _.uniq(_.flatten(_.map(packages_data, function(pkg) {
        return _.map(pkg.recipies, function(r) { return r.repo.bintray.split('/').splice(0, 2).join('/'); })
    })));
    $('#numRemotes').html(repos.length);

    String.prototype.toTitleCase = function() {
        return this[0].toUpperCase() + this.substr(1);
    };

    var App = {
        templates: {
            pkgResult: _.template($('#packageItemTemplate').html()),
            pkg: _.template($('#packageTemplate').html()),
            category: _.template($('#categoryTemplate').html())
        },
        searchIndex: new Fuse(packages_data, {
            id: 'id',
            shouldSort: true,
            threshold: 0.3,
            location: 0,
            distance: 100,
            maxPatternLength: 32,
            minMatchCharLength: 2,
            includeMatches: true,
            keys: [
                {
                    "name": "name",
                    "weight": 0.5
                },
                {
                    "name": "description",
                    "weight": 0.2
                },
                {
                    "name": "keywords",
                    "weight": 0.3
                }
            ]
        }),
        showPackagesInResult: function(ids) {
            $('.package_result').removeClass('hidden');
            if (ids.length === 0) {
                $('.package_result:not(.disabled)').addClass('hidden');
            } else {
                var $results = $('#results');
                $results.find('> a:not(' + _.map(ids, function(id) { return '#package_' + id; }).join(',') + ')').addClass('hidden');
                var allResults = $results.children('a:not(.hidden)');
                var mappedResults = {};
                allResults.detach().each(function(i, e) {
                    mappedResults[e.id.replace('package_', '')] = e;
                });
                $results.append(_.map(ids, function(id) { return mappedResults[id]; }));
                $results.find('a:not(.disabled)').removeClass('rounded-top').removeClass('rounded-bottom');
                $results.find('#package_' + ids[0]).addClass('rounded-top');
                $results.find('#package_' + ids[ids.length-1]).addClass('rounded-bottom');
            }
        },
        highlightSearchTerms: function(terms) {
            var prepend = '<span class="highlighted_search_term">';
            var append = '</span>';

            $('span.highlighted_search_term').parent().each(function(index, elem) {
                var $elem = $(elem);
                $elem.html($elem.html().replace(new RegExp(prepend, 'g'), '').replace(new RegExp(append, 'g'), ''));
            });

            _.each(terms, function(result) {
                var $item = $('#package_' + result.item);
                _.each(result.matches, function(match) {
                    var $attribute = $item.find('.attribute_' + match.key);
                    if ($attribute.length > 0) {
                        var content = $attribute.html();
                        var indices = match.indices;
                        // make the last come first
                        indices.sort(function(a, b) { return a[0] < b[0]; });
                        _.each(indices, function(index) {
                            content = content.substr(0, index[0]) +
                                prepend + content.substr(index[0], index[1]+1-index[0]) + append +
                                    content.substr(index[1]+1);
                        });
                        $attribute.html(content);
                    }
                });
            });
        },
        showResultsForFilter: function(filter) {
            if (filter === '') {
                this.highlightSearchTerms([]);
                this.showPackagesInResult(_.map(packages_data, _.property('id')));
            } else {
                var results = this.searchIndex.search(filter);
                this.showPackagesInResult(_.map(results, _.property('item')));
                this.highlightSearchTerms(results);
            }
        },
        router: new Navigo(null, true, '#!'),
        $searchInput: $('#searchInput'),
        setState: function(state) {
            if (state === 'home' || state === 'search') {
                $('#search').show();
                $('#package').hide();
                $('#category').hide();
            } else if (state === 'package') {
                $('#search').hide();
                $('#package').show();
                $('#category').hide();
            } else if (state == 'category') {
                $('#search').hide();
                $('#package').hide();
                $('#category').show();
            }
        },
        pkgView: {
            showFile: function(file) {
                return;
                $('[data-filekey]:not(.nav-link)').hide();
                $('[data-filekey=' + file + ']:not(.nav-link)').show();
                $('.nav-link[data-filekey]').removeClass('active');
                $('.nav-link[data-filekey=' + file + ']').addClass('active');
            }
        },
        updateCurrentVersion: function(select) {
            var $select = $(select);
            var pkg = _.find(packages_data, function(p) { return p.name === $select.attr('data-package'); });
            var version = pkg.versions[$select.val()];

            var $container = $select.parent();
            $container.find('[data-field]').each(function(index, element) {
                var $element = $(element);
                $element.html(version[$element.attr('data-field')]);
            });
        },
        categoryLink: function(part, noLink) {
            if (noLink) {
                return part.name;
            }
            return '<a href="' + this.router.generate('category', {name: part.id}) + '">' + part.name + '</a>';
        },
        readableCategory: function(category, onlyLeaf, noLink) {
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
                'rpc': 'RPC'
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
                        return this.categoryLink(parts[1], noLink);
                    } else {
                        return parts[1].name + this.categoryLink(parts[2], noLink);
                    }
                } else {
                    if (parts.length === 2) {
                        return 'Standard: ' + this.categoryLink(parts[1]);
                    } else {
                        return 'Standard: ' + this.categoryLink(parts[1]) + this.categoryLink(parts[2]);
                    }
                }
            } else if (category.startsWith('status.')) {
                parts[1].name = parts[1].name.substr(1).toTitleCase();
                if (onlyLeaf) {
                    return this.categoryLink(parts[1], noLink);
                }
                return 'Status: ' + this.categoryLink(parts[1]);
            } else if (category.startsWith('environment.')) {
                if (onlyLeaf) {
                    return parts[1];
                }
                return 'Environment: ' + parts[1];
            } else if (category.startsWith('topic.')) {
                if (parts.length > 2) {
                    var ret = parts[1].name + ': ';
                    parts = _.map(parts.splice(2), function(p) { return App.categoryLink(p, noLink); });
                    if (onlyLeaf) {
                        return parts[parts.length-1];
                    }
                    return ret + parts.join(' &gt; ');
                } else {
                    return parts[1].name;
                }
            }
            return category;
        },
        categoryFilter: function(categories) {
            return _.filter(categories, function(cat) {
                var subs = _.filter(categories, function(subcat) { return subcat.startsWith(cat + '.'); });
                return subs.length === 0;
            });
        },
        allCategories: _.chain(packages_data).map(_.property('categories')).flatten().uniq().value(),
        forCategory: function(subcat, includeSubs) {
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
        },
        readableStandards: function(categories) {
            var standards = _.chain(this.categoryFilter(categories))
                .filter(function(cat) { return cat.startsWith('standard.'); })
                .map(function(cat) { return cat.replace('standard.', '').replace('cpp', 'c++').toTitleCase(); })
                .sortBy(function(cat) { // order by year
                    var parts = cat.split('.');
                    var result = 0;
                    if (parts[0] === 'C') {
                        result = 10000;
                    } else if (parts[0] === 'C++') {
                        result = 20000;
                    }

                    if (parts.length >= 2) {
                        var shortYear = parseInt(cat.split('.')[1]);
                        result += shortYear;
                        result += shortYear > 70 ? 1900 : 2000;
                    }

                    return result;
                })
                .map(function(cat) { return cat.replace('.', ''); })
                .value().join('/');

            return standards;
        }
    };

    function searchHandler(params) {
        App.setState('search');

        if (!params) {
            params = {query: ''}
        }
        App.showResultsForFilter(params.query);
        if (App.$searchInput.val() !== params.query) {
            App.router.pause();
            App.$searchInput.val(params.query);
            App.router.resume();
        }
    }

    App.router.on(function() {
        searchHandler({query: ''});
    }).on({
        '': searchHandler,
        'search/:query': {as: 'search', uses: searchHandler},
        'search': searchHandler,
        'package/:id': {as: 'package', uses: function(params) {
            App.setState('package');
            var $package = $('#package');
            var pkgData = _.find(packages_data, function(pkg) { return pkg.id === params.id; });
            $package.html(App.templates.pkg(pkgData));
            timeago().render($package.find('.timeago'));
            $package.find('pre > code').each(function(i, block) {
                hljs.highlightBlock(block);
            });
            var versionSelector = $package.find('.version-selector');
            App.updateCurrentVersion(versionSelector);
            versionSelector.on('change input', function(evt) { App.updateCurrentVersion(evt.target); });
            scrollTo(0, 0);
        }},
        'category/:name': {as: 'category', uses: function(params) {
            App.setState('category');
            var $category = $('#category');
            $category.html(App.templates.category({
                category: params.name,
                subcats: _.filter(App.allCategories, function(c) {
                    var a = c.split('.');
                    var b = params.name.split('.');
                    return c.startsWith(params.name + '.') && a.length === b.length+1;
                })
            }));
            scrollTo(0, 0);
        }}
    });

    App.$searchInput.on('keyup change focusout paste propertychange', function() {
        App.router.navigate(App.router.generate('search', {query: App.$searchInput.val()}));
    });

    window.App = App;

    var $results = $('#results');
    _.each(packages_data, function(pkg) {
        $results.append(App.templates.pkgResult(_.extend({noTags: false}, pkg)));
    });

    App.router.resolve();
});
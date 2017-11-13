$(function() {
    $('#numPackages').html(packages_data.length);

    var App = {
        templates: {
            pkgResult: _.template($('#packageItemTemplate').html()),
            pkg: _.template($('#packageTemplate').html())
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
                $('.package_result.disabled').addClass('hidden');
            } else {
                var $results = $('#results');
                $results.find('> a:not(' + _.map(ids, function(id) { return '#package_' + id; }).join(',') + ')').addClass('hidden');
                var allResults = $results.children('a:not(.hidden)');
                var mappedResults = {};
                allResults.detach().each(function(i, e) {
                    mappedResults[e.id.replace('package_', '')] = e;
                });
                $results.append(_.map(ids, function(id) { return mappedResults[id]; }));
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
                $('#results, #information, #searchInput').show();
                $('#package').hide();
            } else if (state === 'package') {
                $('#results, #information, #searchInput').hide();
                $('#package').show();
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
            scrollTo(0, 0);
            //$package.find('.nav-tabs > a:first-of-type').tab('show');
        }}
    });

    App.$searchInput.on('keyup change focusout paste propertychange', function() {
        App.router.navigate(App.router.generate('search', {query: App.$searchInput.val()}));
    });

    window.App = App;

    var $results = $('#results');
    _.each(packages_data, function(pkg) {
        $results.append(App.templates.pkgResult(pkg));
    });

    App.router.resolve();
});
$('#numPackages').html(packages_data.length);
var repos = _.uniq(_.flatten(_.map(packages_data, function(pkg) {
    return _.map(pkg.recipies, function(r) { return r.repo.bintray.split('/').splice(0, 2).join('/'); })
})));
$('#numRemotes').html(repos.length);

var $results = $('#results');
_.each(packages_data, function(pkg) {
    $results.append(App.templates.pkgResult(_.extend({noTags: false}, pkg)));
});

App.search = {};
App.search.$ = $('#searchView');
App.search.$results = App.search.$.find('#results');
App.search.searchIndex = new Fuse(packages_data, {
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
});
App.search.showPackagesInResult = function(ids) {
    $('.package_result').removeClass('hidden');
    if (ids.length === 0) {
        $('.package_result:not(.disabled)').addClass('hidden');
    } else {
        $('.package_result.disabled').addClass('hidden');
        var $results = App.search.$results;
        if (ids.length !== packages_data.length) {
            $results.find('> a:not(' + _.map(ids, function (id) {
                return '#package_' + id;
            }).join(',') + ')').addClass('hidden');
            var allResults = $results.children('a:not(.hidden)');
            var mappedResults = {};
            allResults.detach().each(function (i, e) {
                mappedResults[e.id.replace('package_', '')] = e;
            });
            $results.append(_.map(ids, function (id) {
                return mappedResults[id];
            }));
        }
        $results.find('a:not(.disabled)').removeClass('rounded-top').removeClass('rounded-bottom');
        $results.find('#package_' + ids[0]).addClass('rounded-top');
        $results.find('#package_' + ids[ids.length-1]).addClass('rounded-bottom');
    }
};
App.search.highlightSearchTerms = function(terms) {
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
};
App.search.showResultsForFilter = function(filter) {
    if (filter === '') {
        this.highlightSearchTerms([]);
        this.showPackagesInResult(_.map(packages_data, _.property('id')));
    } else {
        var results = this.searchIndex.search(filter);
        this.showPackagesInResult(_.map(results, _.property('item')));
        this.highlightSearchTerms(results);
    }
};
App.search.$input = $('#searchInput');

App.search.$input.on('keyup change focusout paste propertychange', function() {
    App.router.navigate(App.router.generate('search', {query: App.search.$input.val()}));
});
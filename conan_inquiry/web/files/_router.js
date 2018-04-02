App.router = new Navigo(null, true, '#!');

function searchHandler(params) {
    App.setState('search');

    if (!params) {
        params = {query: ''}
    }
    App.search.showResultsForFilter(params.query);
    if (App.search.$input.val() !== params.query) {
        App.router.pause();
        App.search.$input.val(params.query);
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
        var pkgData = _.find(packages_data, function(pkg) { return pkg.id === params.id; });
        App.package.$.html(App.templates.pkg(pkgData));
        timeago().render(App.package.$.find('.timeago'));
        App.package.$.find('pre > code').each(function(i, block) {
            hljs.highlightBlock(block);
        });
        var versionSelector = App.package.$.find('.version-selector');
        App.package.updateCurrentVersion(versionSelector);
        versionSelector.on('change input', function(evt) { App.package.updateCurrentVersion(evt.target); });
    }},
    'category/:name': {as: 'category', uses: function(params) {
        App.setState('category');
        var subcats = _.filter(App.category.allUnique, function(c) {
            var a = c.split('.');
            var b = params.name.split('.');
            return c.startsWith(params.name + '.') && a.length === b.length+1;
        });
        if (params.name.startsWith('standard.')) {
            subcats = App.category.sortStandards(subcats);
        }
        App.category.$.html(App.templates.category({
            category: params.name,
            subcats: subcats
        }));
    }},
    'stats': {as: 'stats', uses: function(params) {
        App.setState('statistics');
    }},
    'remote/:owner/:repo': {as: 'remote', uses: function(params) {
        App.setState('remote');
        App.remote.$.html(App.templates.remote({
            remote: (params.owner + '/' + params.repo)
        }));
    }},
    '': searchHandler
});

App.router.goto = function(route, params) {
    return this.navigate(this.generate(route, params));
}
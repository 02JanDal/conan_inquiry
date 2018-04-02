App.remote = {};
App.remote.$ = $('#remoteView');
App.remote.forRemote = function(remote) {
    return _.chain(packages_data).filter(function(pkg) {
        return _.find(pkg.recipies, function(rec) { return rec.repo.bintray.startsWith(remote + '/'); })
    }).sortBy(function(pkg) { return pkg.name; }).value();
};
App.remote.all = _.chain(packages_data).map(function(pkg) {
    return _.map(pkg.recipies, function(r) { return r.repo.bintray.split('/').splice(0, 2).join('/'); });
}).flatten().value();
App.remote.allUnique = _.uniq(App.remote.all).sort();
App.remote.counts = _.countBy(App.remote.all, _.identity);
App.remote.sortedCounts = _.chain(App.remote.counts)
    .map(function(count, key) { return [key, count]; })
    .sortBy(function(r) { return r[1]; }).value();

var $menuRemote = $('[data-menu-remote]');
_.each(App.remote.allUnique, function(remote) {
    var parts = remote.split('/');
    $menuRemote.append(App.templates.menuItem({
        name: remote,
        href: App.router.generate('remote', {owner: parts[0], repo: parts[1]}),
        count: App.remote.counts[remote]
    }));
});

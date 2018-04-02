var hues = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink'];
hues = hues.concat(hues); hues = hues.concat(hues); hues = hues.concat(hues);
function getSunburstCategoryData(prefix) {
    var prefixPartCount = prefix.split('.').length;
    // get direct children:
    var children = _.filter(App.category.allUnique, function(cat) {
        return cat.startsWith(prefix) && cat.split('.').length === prefixPartCount;
    });
    var category = prefix.substr(0, prefix.length-1);
    var name = App.category.readable(category, true, true);
    if (children.length === 0) {
        return {
            name: name,
            id: category,
            value: App.category.counts[category]
        };
    } else {
        return {
            name: name,
            id: category,
            hue: hues.pop(),//randomColor({seed: category}),
            children: _.map(children, function(cat) { return getSunburstCategoryData(cat + '.'); })
        };
    }
}

function setupSunburst(selector, data) {
    var $element = $(selector);
    var element = $element[0];
    var chart = new Sunburst();
    chart.data(data).width(element.offsetWidth).height(element.offsetHeight)(element);
    chart.color(function(node, parent) {
        var baseLevel = -1;
        if (node.id.startsWith('topic.tool')) {
            baseLevel = 2;
        } else if (node.id.startsWith('topic.library')) {
            baseLevel = 3;
        } else if (node.id.startsWith('standard.')) {
            baseLevel = 1;
        }

        if (node.id.split('.').length < baseLevel || !parent) {
            return randomColor({
                hue: 'monochrome',
                luminosity: 'bright'
            });
        }

        var subTopic = {data: node, parent: parent};
        while (subTopic.data.id.split('.').length > baseLevel) {
            subTopic = subTopic.parent;
        }

        return randomColor({
            hue: subTopic.data.hue,
            luminosity: 'bright',
            format: 'rgba',
            alpha: 1/(Math.max(1, parent.depth-2)*1.5)
        });
    });
    $(window).resize(function(evt) {
        chart.width(element.offsetWidth).height(element.offsetHeight);
    });
}

App.statistics = {};
App.statistics.$ = $('#statisticsView');
App.initialized = false;
App.statistics.onEnter = function() {
    if (this.initialized) {
        return;
    }
    this.initialized = true;

    console.debug('setting up graphs');

    setupSunburst(document.getElementById('chartA'), getSunburstCategoryData('topic.'));
    setupSunburst(document.getElementById('chartB'), getSunburstCategoryData('standard.'));

    var onClickVisit = {
        library: {
            onClick: function(event, elements) {
                var remote = elements[0]._model.label.split('/');
                App.router.goto('remote', {owner: remote[0], repo: remote[1]});
            }
        }
    };

    var counts = {};
    _.each(packages_data, function(pkg) {
        _.each(pkg.versions, function(version) {
            var repo = version.repo.split('/').splice(0, 2).join('/');
            if (!counts[repo]) {
                counts[repo] = 1;
            } else {
                counts[repo]++;
            }
        });
    });
    counts = _.chain(counts).map(function(count, repo) { return [repo, count]; }).sortBy(function(arr) { return arr[1]; }).value();

    new Chartkick.BarChart('chartC', App.remote.sortedCounts.reverse(), onClickVisit);
    new Chartkick.BarChart('chartD', counts.reverse(), onClickVisit)
};
App.statistics.onEntered = function() {
    $(window).trigger('resize');
};

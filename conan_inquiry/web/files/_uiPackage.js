App.package = {};
App.package.$ = $('#packageView');
App.package.showFile = function(file) {
    return;
    $('[data-filekey]:not(.nav-link)').hide();
    $('[data-filekey=' + file + ']:not(.nav-link)').show();
    $('.nav-link[data-filekey]').removeClass('active');
    $('.nav-link[data-filekey=' + file + ']').addClass('active');
};
App.package.updateCurrentVersion = function(select) {
    var $select = $(select);
    var pkg = _.find(packages_data, function(p) { return p.name === $select.attr('data-package'); });
    var version = pkg.versions[$select.val()];

    var $container = $select.parent();
    $container.find('[data-field]').each(function(index, element) {
        var $element = $(element);
        $element.html(version[$element.attr('data-field')]);
    });
};
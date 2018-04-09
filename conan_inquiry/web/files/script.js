//import _utility.js

var App = {};

App.templates = {
    pkgResult: _.template($('#packageItemTemplate').html()),
    pkg: _.template($('#packageTemplate').html()),
    category: _.template($('#categoryTemplate').html()),
    remote: _.template($('#remoteTemplate').html()),
    menuItem: _.template($('#menuItemTemplate').html()),
    findingManyRemotes: _.template($('#findingManyRemotes').html())
};
App.setState = function(state) {
    console.debug('New state:', state);

    if (state in App && App[state].onEnter) {
        App[state].onEnter();
    }

    $('[data-state]').hide();
    $('[data-state=' + state + ']').show();

    scrollTo(0, 0);

    if (state in App && App[state].onEntered) {
        App[state].onEntered();
    }
};

window.App = App;

//import _router.js

//import _uiCategory.js
//import _uiSearch.js
//import _uiPackage.js
//import _uiRemote.js
//import _uiStatistics.js

$(function() {
    App.router.resolve();
});
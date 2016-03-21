var loomApp = angular.module('loomApp', [
    'ui.router',
    'loomControllers']);

loomApp.config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/runs');

    $stateProvider
        .state('runs', {
            url:'/runs',
            templateUrl: 'partials/run-list.html',
            controller: 'RunListCtrl'
        })
        .state('runs.run', {
            url:'/{workflowId}',
            templateUrl: 'partials/run-detail.html',
            controller: 'RunDetailCtrl'
        })
        .state('runs.run.step', {
            url:'/{stepId}', 
            templateUrl: 'partials/step-detail.html',
            controller: 'StepDetailCtrl'
        })
        .state('files', {
            url:'/files', 
            templateUrl: 'partials/files-list.html',
            controller: 'FilesListCtrl'
        });
}]);

// Define a service which we will use to pass data between controllers
loomApp.factory('$loom', function() {
    var loomServiceScope = {};
    return loomServiceScope;
});

var loomApp = angular.module('loomApp', [
    'ui.router',
    'loomControllers']);

loomApp.config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/runs');

    $stateProvider
        .state('runs', {
            url: '/runs',
            templateUrl: 'partials/run-list.html',
            controller: 'RunListCtrl'
        })
        .state('runs.run', {
            url: '/{workflowRunId}',
            templateUrl: 'partials/run-detail.html',
            controller: 'RunDetailCtrl'
        })
        .state('runs.run.step', {
            url: '/{stepId}', 
            templateUrl: 'partials/run-step-detail.html',
            controller: 'RunStepDetailCtrl'
        })
        .state('workflows', {
            url: '/workflows',
            templateUrl: 'partials/workflow-list.html',
            controller: 'WorkflowListCtrl'
        })
        .state('workflows.workflow', {
            url: '/{workflowId}',
            templateUrl: 'partials/workflow-detail.html',
            controller: 'WorkflowDetailCtrl'
        })
        .state('workflows.workflow.step', {
            url: '/steps/{stepId}',
            templateUrl: 'partials/workflow-step-detail.html',
            controller: 'WorkflowStepDetailCtrl'
        })
        .state('files', {
            url:'/files', 
            templateUrl: 'partials/file-list.html',
            controller: 'FileListCtrl'
        });
}]);

// Define a service which we will use to pass data between controllers
loomApp.factory('$loom', function() {
    var loomServiceScope = {};
    return loomServiceScope;
});

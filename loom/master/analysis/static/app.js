var loomApp = angular.module('loomApp', [
    'ui.router',
    'loomControllers']);

loomApp.config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/workflows');

    $stateProvider
        .state('workflows', {
            url:'/workflows',
            templateUrl: 'partials/workflow-list.html',
            controller: 'WorkflowListCtrl'
        })
        .state('workflows.workflow', {
            url:'/{workflowId}',
            templateUrl: 'partials/workflow-detail.html',
            controller: 'WorkflowDetailCtrl'
        })
        .state('workflows.workflow.step', {
            url:'/{stepId}', 
            templateUrl: 'partials/step-detail.html',
            controller: 'StepDetailCtrl'
        });
}]);

// Define a service which we will use to pass data between controllers
loomApp.factory('$loom', function() {
    var loomServiceScope = {};
    return loomServiceScope;
});

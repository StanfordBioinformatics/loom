var loomApp = angular.module('loomApp', [
    'ngRoute',
    'loomControllers']);

loomApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/workflows', {
        templateUrl: 'partials/workflow-list.html',
        controller: 'WorkflowListCtrl'
      }).
      when('/workflows/:workflowId', {
        templateUrl: 'partials/workflow-detail.html',
        controller: 'WorkflowDetailCtrl'
      }).
      otherwise({
        redirectTo: '/workflows'
      });
  }]);

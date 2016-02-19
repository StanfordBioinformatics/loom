var loomControllers = angular.module('loomControllers', []);

loomControllers.controller('WorkflowListCtrl', ['$scope', '$http',
    function ($scope, $http) {
        // Query the Loom server API for workflows. Assumes same server.
        // May need to watch out for same-origin policy / cross-site scripting restrictions if
        // this page is hosted in a different location than the Loom server.
        $http.get('http://' + window.location.host + '/api/workflows').success(function(data) {
            $scope.workflows = data;
            //console.log('got workflows:');
            //console.log(data);
        });
    }]);

loomControllers.controller('WorkflowDetailCtrl', ['$scope', '$routeParams',
  function($scope, $routeParams) {
    $scope.workflowId = $routeParams.workflowId;
  }]);


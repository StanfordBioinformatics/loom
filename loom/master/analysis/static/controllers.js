var loomControllers = angular.module('loomControllers', []);

loomControllers.controller('BreadcrumbCtrl', ['$scope', '$loom', '$state',
    function ($scope, $loom, $state) {
        $scope.$state = $state;
        $scope.$loom = $loom;
    }]);

loomControllers.controller('WorkflowListCtrl', ['$scope', '$http', '$loom', '$state',
    function ($scope, $http, $loom, $state) {
        // Query the Loom server API for workflows. Assumes same server.
        // May need to watch out for same-origin policy / cross-site scripting restrictions if
        // this page is hosted in a different location than the Loom server.
        $http.get('http://' + window.location.host + '/api/workflow_runs').success(function(response) {
            $loom.workflow_runs = response['workflow_runs'];
            $scope.workflow_runs = $loom.workflow_runs;
        });
        $scope.$state = $state;
    }]);

loomControllers.controller('WorkflowDetailCtrl', ['$scope', '$http', '$loom', '$stateParams', 
    function($scope, $http, $loom, $stateParams) {
        $http.get('http://' + window.location.host + '/api/workflow_runs/' + $stateParams.workflowId).success(function(response) {
            $loom.workflow_run = response;
            $scope.workflow_run = $loom.workflow_run;
        });
    }]);

loomControllers.controller('StepDetailCtrl', ['$scope', '$http', '$loom', '$stateParams',
    function($scope, $http, $loom, $stateParams) {
        /*
        $http.get('http://' + window.location.host + '/api/steps/' + $stateParams.stepId).success(function(response) {
            $loom.step = response;
            $scope.stepId = $stateParams.stepId;
        });
        */
        $loom.stepId = $stateParams.stepId;
        $scope.stepId = $loom.stepId;
    }]);

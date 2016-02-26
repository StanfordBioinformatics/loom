var loomControllers = angular.module('loomControllers', []);

loomControllers.controller('SidebarCtrl', ['$scope', '$state',
    function($scope, $state) {
        $scope.$state = $state;
    }]);

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
        $http.get('http://' + window.location.host + '/api/step_runs/' + $stateParams.stepId).success(function(response) {
            $loom.step_run = response;
            $scope.step_run = $loom.step_run;
        });
    }]);

loomControllers.controller('FilesListCtrl', ['$scope', '$http', '$loom', '$state',
    function($scope, $http, $loom, $state) {
        $http.get('http://' + window.location.host + '/api/data_source_records').success(function(response) {
            files = [];
            records = response['data_source_records'];
            records.forEach(function(record) {
                record.data_objects.forEach(function(data_object) {
                    data_object.datetime_updated = record.datetime_updated;
                    data_object.datetime_created = record.datetime_created;
                    data_object.source_description = record.source_description;
                    files.push(data_object); 
                    console.log(data_object);
                });
            });
            $loom.files = files;
            $scope.files = $loom.files;
        });
    }]);

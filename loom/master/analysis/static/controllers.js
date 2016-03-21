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

loomControllers.controller('RunListCtrl', ['$scope', '$http', '$loom', '$state',
    function ($scope, $http, $loom, $state) {
        $http.get('/api/workflow_runs').success(function(response) {
            $loom.workflow_runs = response['workflow_runs'];
            $scope.workflow_runs = $loom.workflow_runs;
        });
        $scope.$state = $state;
    }]);

loomControllers.controller('RunDetailCtrl', ['$scope', '$http', '$loom', '$stateParams', 
    function($scope, $http, $loom, $stateParams) {
        $http.get('/api/workflow_runs/' + $stateParams.workflowId).success(function(response) {
            $loom.workflow_run = response;
            $scope.workflow_run = $loom.workflow_run;
        });
    }]);

loomControllers.controller('StepDetailCtrl', ['$scope', '$http', '$loom', '$stateParams',
    function($scope, $http, $loom, $stateParams) {
        $http.get('/api/step_runs/' + $stateParams.stepId).success(function(response) {
            $loom.step_run = response;
            $scope.step_run = $loom.step_run;
        });
    }]);

loomControllers.controller('FilesListCtrl', ['$scope', '$http', '$loom', '$state',
    function($scope, $http, $loom, $state) {
        $http.get('/api/file_data_objects').success(function(response) {
	    files = response['file_data_objects'];
	    $loom.files = files;
            $scope.files = $loom.files;

	    $scope.files.forEach(function(file) {
		$http.get('/api/file_data_objects/' + file._id + '/data_source_records/').then(function(response){
		    file['data_source_records'] = response['data']['data_source_records'];
		});
		$http.get('/api/file_data_objects/' + file._id + '/file_storage_locations/').then(function(response){
		    file['file_storage_locations'] = response['data']['file_storage_locations'];
		    console.log($scope);
		});
	    });
        });
    }]);

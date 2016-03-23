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
					       console.log('runlist');
        $http.get('/api/workflow_runs').success(function(response) {
            $loom.workflow_runs = response['workflow_runs'];
            $scope.workflow_runs = $loom.workflow_runs;
        });
        $scope.$state = $state;
    }]);

loomControllers.controller('RunDetailCtrl', ['$scope', '$http', '$loom', '$stateParams',
    function($scope, $http, $loom, $stateParams) {
        $http.get('/api/workflow_runs/' + $stateParams.workflowRunId).success(function(response) {
            $loom.workflow_run = response;
            $scope.workflow_run = $loom.workflow_run;
        });
    }]);

loomControllers.controller('WorkflowListCtrl', ['$scope', '$http', '$loom', '$state',
    function($scope, $http, $loom, $state){
	$http.get('/api/workflows').success(function(response) {
	    $loom.workflows = response['workflows'];
	    $scope.workflows = $loom.workflows;
	});
	$scope.$state = $state;
    }]);

loomControllers.controller('WorkflowDetailCtrl', ['$scope', '$http', '$loom', '$stateParams', 
    function($scope, $http, $loom, $stateParams) {
        $http.get('/api/workflows/' + $stateParams.workflowId).success(function(response) {
            $loom.workflow = response;
            $scope.workflow = $loom.workflow;
        });
    }]);

loomControllers.controller('RunStepDetailCtrl', ['$scope', '$http', '$loom', '$stateParams',
    function($scope, $http, $loom, $stateParams) {
        $http.get('/api/step_runs/' + $stateParams.stepId).success(function(response) {
            $loom.step_run = response;
            $scope.step_run = $loom.step_run;
        });
    }]);

loomControllers.controller('FileListCtrl', ['$scope', '$http', '$loom', '$state',
    function($scope, $http, $loom, $state) {
        $http.get('/api/file_data_objects').success(function(response) {
	    $loom.files = response['file_data_objects'];
            $scope.files = $loom.files;

	    $scope.files.forEach(function(file) {
		$http.get('/api/file_data_objects/' + file._id + '/data_source_records/').then(function(response){
		    file['data_source_records'] = response['data']['data_source_records'];
		});
		$http.get('/api/file_data_objects/' + file._id + '/file_storage_locations/').then(function(response){
		    file['file_storage_locations'] = response['data']['file_storage_locations'];
		});
	    });
        });
	$scope.$state = $state;
    }]);

'use strict';

angular
    .module('loom.controllers')
    .controller('RunDetailController', RunDetailController);

RunDetailController.$inject = [
    '$scope', '$http', 'Data', '$stateParams'
];

function RunDetailController($scope, $http, Data, $stateParams) {
    $http.get('/api/workflow_runs/' + $stateParams.workflowRunId)
	.success(function(response) {
	    Data.workflow_run = response;
	    $scope.workflow_run = Data.workflow_run;
	});
};

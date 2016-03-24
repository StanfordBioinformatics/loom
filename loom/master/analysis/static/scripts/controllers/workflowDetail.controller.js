'use strict';

angular
    .module('loom.controllers')
    .controller('WorkflowDetailController', WorkflowDetailController);

WorkflowDetailController.$inject = [
    '$scope', '$http', 'Data', '$stateParams'
];

function WorkflowDetailController($scope, $http, Data, $stateParams) {
    $http.get('/api/workflows/' + $stateParams.workflowId)
	.success(function(response) {
	    Data.workflow = response;
	    $scope.workflow = Data.workflow;
	});
};

'use strict';

angular
    .module('loom.controllers')
    .controller('WorkflowDetailController', WorkflowDetailController);

WorkflowDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function WorkflowDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveWorkflow($routeParams.workflowId).then(function() {
	$scope.loading = false;
    });
};

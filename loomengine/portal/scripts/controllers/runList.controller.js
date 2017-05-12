'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService'];

function RunListController($scope, DataService) {
    $scope.loading = true;
    DataService.getRunWorkflowsExpanded().then(function(runs) {
	    $scope.loading = false;
	    $scope.runs = runs;
    });
};

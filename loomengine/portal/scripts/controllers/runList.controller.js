'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService', '$location'];

function RunListController($scope, DataService, $location) {
    $scope.$location = $location;
    $scope.loading = true;
    DataService.getRunWorkflowsExpanded().then(function(runs) {
	    $scope.loading = false;
	    $scope.runs = runs;
    });
};

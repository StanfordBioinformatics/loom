'use strict';

angular
    .module('loom.controllers')
    .controller('RunDetailController', RunDetailController);

RunDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function RunDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveRun($routeParams.runId).then(function() {
	$scope.loading = false;
    });
};

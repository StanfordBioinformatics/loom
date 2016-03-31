'use strict';

angular
    .module('loom.controllers')
    .controller('RunDetailController', RunDetailController);

RunDetailController.$inject = [
    '$scope', 'DataService', '$state', '$stateParams'
];

function RunDetailController($scope, DataService, $state, $stateParams) {
    $scope.$state = $state;
    $scope.loading = true;
    DataService.setActiveRun($stateParams.runId).then(function() {
	$scope.loading = false;
	$scope.activeData = DataService.getActiveData();
    });
};

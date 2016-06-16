'use strict';

angular
    .module('loom.controllers')
    .controller('DataDetailController', DataDetailController);

DataDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function DataDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveData($routeParams.dataId).then(function() {
	$scope.loading = false;
    });
};

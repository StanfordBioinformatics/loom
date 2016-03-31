'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService', '$state'];

function RunListController($scope, DataService, $state) {
    $scope.$state = $state;
    $scope.loading = true;
    DataService.getRuns().then(function(runs) {
	$scope.loading = false;
	$scope.runs = runs;
    });
};

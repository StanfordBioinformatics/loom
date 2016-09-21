'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService'];

function RunListController($scope, DataService) {
    $scope.loading = true;
    DataService.getRunRequests().then(function(run_requests) {
	$scope.loading = false;
	$scope.run_requests = run_requests;
    });
};

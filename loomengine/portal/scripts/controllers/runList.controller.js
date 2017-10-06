'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService', '$location'];

function RunListController($scope, DataService, $location) {
    function loadRuns() {
	var offset = ($scope.currentPage - 1) * $scope.pageSize
	DataService.getRuns($scope.pageSize, offset).then(function(data) {
	    $scope.runs = data.results;
	    $scope.totalItems = data.count;
	    $scope.loading = false;
	});
    }
    $scope.$location = $location;
    $scope.pageSize = 10;
    $scope.loading = true;
    $scope.$watch('currentPage', loadRuns, true);
    $scope.currentPage= 1;
};

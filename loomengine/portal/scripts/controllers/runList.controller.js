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
	    $scope.total = data.count;
	    $scope.loading = false;
	});
    }
    $scope.$location = $location;
    $scope.$watch('currentPage', loadRuns, true);
    $scope.pageSize = 10;
    $scope.currentPage=1;
    $scope.loading = true;
    loadRuns();
};

'use strict';

angular
    .module('loom.controllers')
    .controller('ResultFileListController', ResultFileListController);

ResultFileListController.$inject = ['$scope', 'DataService'];

function ResultFileListController($scope, DataService){
    function loadFiles() {
	var offset = ($scope.currentPage - 1) * $scope.pageSize
	DataService.getResultFiles($scope.pageSize, offset).then(function(data) {
	    $scope.files = data.results;
	    $scope.totalItems = data.count;
	    $scope.loading = false;
	});
    }
    $scope.pageSize = 10;
    $scope.loading = true;
    $scope.$watch('currentPage', loadFiles, true);
    $scope.currentPage = 1;
};

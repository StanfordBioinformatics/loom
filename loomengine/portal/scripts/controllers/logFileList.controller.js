'use strict';

angular
    .module('loom.controllers')
    .controller('LogFileListController', LogFileListController);

LogFileListController.$inject = ['$scope', 'DataService'];

function LogFileListController($scope, DataService){
    function loadFiles() {
	var offset = ($scope.currentPage - 1) * $scope.pageSize
	DataService.getLogFiles($scope.pageSize, offset).then(function(data) {
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

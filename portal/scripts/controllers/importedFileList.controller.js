'use strict';

angular
    .module('loom.controllers')
    .controller('ImportedFileListController', ImportedFileListController);

ImportedFileListController.$inject = ['$scope', 'DataService'];

function ImportedFileListController($scope, DataService){
    function loadFiles() {
	var offset = ($scope.currentPage - 1) * $scope.pageSize
	DataService.getImportedFiles($scope.pageSize, offset).then(function(data) {
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

'use strict';

angular
    .module('loom.controllers')
    .controller('ImportedFileListController', ImportedFileListController);

ImportedFileListController.$inject = ['$scope', 'DataService'];

function ImportedFileListController($scope, DataService){
    $scope.loading = true;
    DataService.getImportedFiles().then(function(imported_files) {
	$scope.loading = false;
	$scope.imported_files = imported_files;
    });
};    



'use strict';

angular
    .module('loom.controllers')
    .controller('ImportedFileListController', ImportedFileListController);

ImportedFileListController.$inject = ['$scope', 'DataService'];

function ImportedFileListController($scope, DataService){
    $scope.loading = true;
    DataService.getImportedFiles().then(function(files) {
	$scope.loading = false;
	$scope.files = files;
    });
};    

'use strict';

angular
    .module('loom.controllers')
    .controller('FileListController', FileListController);

FileListController.$inject = ['$scope', 'DataService'];

function FileListController($scope, DataService){
    $scope.loading = true;
    DataService.getFiles().then(function(files) {
	$scope.loading = false;
	$scope.files = files;
    });
};    



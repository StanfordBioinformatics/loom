'use strict';

angular
    .module('loom.controllers')
    .controller('LogFileListController', LogFileListController);

LogFileListController.$inject = ['$scope', 'DataService'];

function LogFileListController($scope, DataService){
    $scope.loading = true;
    DataService.getLogFiles().then(function(files) {
	$scope.loading = false;
	$scope.files = files;
    });
};    

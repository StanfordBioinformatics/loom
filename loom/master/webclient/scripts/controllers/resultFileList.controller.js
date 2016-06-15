'use strict';

angular
    .module('loom.controllers')
    .controller('ResultFileListController', ResultFileListController);

ResultFileListController.$inject = ['$scope', 'DataService'];

function ResultFileListController($scope, DataService){
    $scope.loading = true;
    DataService.getResultFiles().then(function(result_files) {
	$scope.loading = false;
	$scope.result_files = result_files;
    });
};    



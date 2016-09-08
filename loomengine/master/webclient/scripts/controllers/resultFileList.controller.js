'use strict';

angular
    .module('loom.controllers')
    .controller('ResultFileListController', ResultFileListController);

ResultFileListController.$inject = ['$scope', 'DataService'];

function ResultFileListController($scope, DataService){
    $scope.loading = true;
    DataService.getResultFiles().then(function(files) {
	$scope.loading = false;
	$scope.files = files;
    });
};    



'use strict';

angular
    .module('loom.controllers')
    .controller('ResultFileDetailController', ResultFileDetailController);

ResultFileDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function ResultFileDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getActiveData();
    $scope.loading = true;
    DataService.setActiveResultFile($routeParams.resultFileId).then(function() {
	$scope.loading = false;
    });
    /*DataService.setActiveFileSourceRuns($routeParams.resultFileId);*/
};

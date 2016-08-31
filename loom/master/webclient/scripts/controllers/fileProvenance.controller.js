'use strict';

angular
    .module('loom.controllers')
    .controller('FileProvenanceController', FileProvenanceController);

FileProvenanceController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function FileProvenanceController($scope, DataService, $routeParams) {
    $scope.loading = true;
    DataService.getFileProvenance($routeParams.fileId).then(function(provenanceData) {
	$scope.loading = false;
	$scope.provenanceData = provenanceData;
    });
};

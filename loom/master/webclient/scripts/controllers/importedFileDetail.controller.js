'use strict';

angular
    .module('loom.controllers')
    .controller('ImportedFileDetailController', ImportedFileDetailController);

ImportedFileDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function ImportedFileDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getActiveData();
    $scope.loading = true;
    DataService.setActiveImportedFile($routeParams.importedFileId).then(function() {
	$scope.loading = false;
    });
};

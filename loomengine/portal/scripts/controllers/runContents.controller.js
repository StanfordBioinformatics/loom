'use strict';

angular
    .module('loom.controllers')
    .controller('RunContentsController', RunContentsController);

RunContentsController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function RunContentsController($scope, DataService, $routeParams) {
    $scope.loading = true;
    $scope.expandedRun = DataService.getRunSummary($scope.run.uuid)
	.then(function(run) {
            $scope.loading = false;
            $scope.expandedRun = run;
    });
};

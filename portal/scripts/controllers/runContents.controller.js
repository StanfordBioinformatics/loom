(function () {
   'use strict';

angular
    .module('loom.controllers')
    .controller('RunContentsController', RunContentsController);

RunContentsController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function RunContentsController($scope, DataService, $routeParams) {
    $scope.loading = true;
    $scope.expandedRun = DataService.getRunDetail($scope.run.uuid)
	.then(function(run) {
            $scope.loading = false;
            $scope.expandedRun = run;
    });
};

}());

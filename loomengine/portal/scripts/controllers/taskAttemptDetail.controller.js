'use strict';

angular
    .module('loom.controllers')
    .controller('TaskAttemptDetailController', TaskAttemptDetailController);

TaskAttemptDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function TaskAttemptDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveTaskAttempt($routeParams.taskAttemptId).then(function() {
	$scope.loading = false;
    });
};

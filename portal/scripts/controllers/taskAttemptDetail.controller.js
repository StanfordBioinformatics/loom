(function () {
   'use strict';

angular
    .module('loom.controllers')
    .controller('TaskAttemptDetailController', TaskAttemptDetailController);

TaskAttemptDetailController.$inject = [
    '$scope', 'DataService', '$routeParams', '$location'
];

function TaskAttemptDetailController($scope, DataService, $routeParams, $location) {
    $scope.$location = $location;
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveTaskAttempt($routeParams.taskAttemptId).then(function() {
	$scope.loading = false;
    });
};
}());

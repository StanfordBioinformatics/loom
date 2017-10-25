(function () {
   'use strict';

angular
    .module('loom.controllers')
    .controller('TaskDetailController', TaskDetailController);

TaskDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function TaskDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveTask($routeParams.taskId).then(function() {
	$scope.loading = false;
    });
};
}());

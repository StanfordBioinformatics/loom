'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', '$http', 'Data', '$state'];

function RunListController($scope, $http, Data, $state) {
    $http.get('/api/workflow_runs').success(function(response) {
	Data.workflow_runs = response['workflow_runs'];
	$scope.workflow_runs = Data.workflow_runs;
    });
    $scope.$state = $state;
};

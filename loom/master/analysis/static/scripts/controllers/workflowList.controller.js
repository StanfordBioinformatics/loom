'use strict';

angular
    .module('loom.controllers')
    .controller('WorkflowListController', WorkflowListController);

WorkflowListController.$inject = ['$scope', '$http', 'Data', '$state'];

function WorkflowListController($scope, $http, Data, $state){
    $http.get('/api/workflows').success(function(response) {
	Data.workflows = response['workflows'];
	$scope.workflows = Data.workflows;
    });
    $scope.$state = $state;
};

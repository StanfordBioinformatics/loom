'use strict';

angular
    .module('loom.controllers')
    .controller('RunStepDetailController', RunStepDetailController);

RunStepDetailController.$inject = [
    '$scope', '$http', 'Data', '$stateParams'
];

function RunStepDetailController($scope, $http, Data, $stateParams) {
    $http.get('/api/step_runs/' + $stateParams.stepId)
	.success(function(response) {
	    Data.step_run = response;
	    $scope.step_run = Data.step_run;
	});
};

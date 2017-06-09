'use strict';

angular
    .module('loom.controllers')
    .controller('ProcessListController', ProcessListController);

ProcessListController.$inject = ['$scope', '$location'];

function ProcessListController($scope, $location) {
    $scope.$location = $location;
	$scope.loading = false;
};

'use strict';

angular
    .module('loom.controllers')
    .controller('TemplateDetailController', TemplateDetailController);

TemplateDetailController.$inject = [
    '$scope', 'DataService', '$routeParams'
];

function TemplateDetailController($scope, DataService, $routeParams) {
    $scope.activeData = DataService.getAllActive();
    $scope.loading = true;
    DataService.setActiveTemplate($routeParams.templateId).then(function() {
	$scope.loading = false;
    });
};

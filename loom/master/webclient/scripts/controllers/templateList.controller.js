'use strict';

angular
    .module('loom.controllers')
    .controller('TemplateListController', TemplateListController);

TemplateListController.$inject = ['$scope', 'DataService'];

function TemplateListController($scope, DataService){
    $scope.loading = true;
    DataService.getTemplates().then(function(templates) {
	$scope.loading = false;
	$scope.templates = templates;
    });
};

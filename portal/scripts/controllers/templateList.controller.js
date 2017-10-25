(function () {
   'use strict';

angular
    .module('loom.controllers')
    .controller('TemplateListController', TemplateListController);

TemplateListController.$inject = ['$scope', 'DataService'];

function TemplateListController($scope, DataService){
    function loadTemplates() {
	var offset = ($scope.currentPage - 1) * $scope.pageSize
	DataService.getTemplates($scope.pageSize, offset).then(function(data) {
	    $scope.templates = data.results;
	    $scope.totalItems = data.count;
	    $scope.loading = false;
	});
    }
    $scope.pageSize = 10;
    $scope.loading = true;
    $scope.$watch('currentPage', loadTemplates, true);
    $scope.currentPage = 1;
};
}());

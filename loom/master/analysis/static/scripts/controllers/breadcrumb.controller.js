'use strict';

angular
    .module('loom.controllers')
    .controller('BreadcrumbController', BreadcrumbController);

BreadcrumbController.$inject = ['$scope', 'DataService', '$state', '$stateParams'];

function BreadcrumbController($scope, DataService, $state, $stateParams) {
    $scope.run = DataService.getCurrentRun();
    $scope.$state = $state;
    $scope.$stateParams = $stateParams;
};

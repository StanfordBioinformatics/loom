'use strict';

angular
    .module('loom.controllers')
    .controller('BreadcrumbController', BreadcrumbController);

BreadcrumbController.$inject = ['$scope', 'Data', '$state'];

function BreadcrumbController($scope, Data, $state) {
    $scope.$state = $state;
    $scope.Data = Data;
};

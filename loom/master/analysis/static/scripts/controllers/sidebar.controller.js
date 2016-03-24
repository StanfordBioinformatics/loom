'use strict';

angular
    .module('loom.controllers')
    .controller('SidebarController', SidebarController);

SidebarController.$inject = ['$scope', '$state'];

function SidebarController($scope, $state) {
    $scope.$state = $state;
};

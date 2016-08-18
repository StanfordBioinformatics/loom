'use strict';

angular
    .module('loom.controllers')
    .controller('NavbarController', NavbarController);

NavbarController.$inject = ['$scope', '$location'];

function NavbarController($scope, $location){
    $scope.$location = $location;
};

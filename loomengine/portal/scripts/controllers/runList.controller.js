'use strict';

angular
    .module('loom.controllers')
    .controller('RunListController', RunListController);

RunListController.$inject = ['$scope', 'DataService', '$location'];

function RunListController($scope, DataService, $location) {
    $scope.$location = $location;
    $scope.loading = true;
    $scope.getColorClass = function(status){
	if (status=='Killed' || status=='Failed'){
	    return "bg-danger";
	}
	else if (status=="Finished"){
	    return "bg-info";
	}
	else if (status=="Running"){
	    return "bg-success";
	}
	else if (status=="Waiting"){
	    return "bg-warning";
	}
	else {
	    return "";
	}
    }
    DataService.getRuns().then(function(runs) {
	    $scope.loading = false;
	    $scope.runs = runs;
    });
};

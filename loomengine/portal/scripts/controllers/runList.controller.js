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
	    return "error";
	}
	else if (status=="Finished"){
	    return "info";
	}
	else if (status=="Running"){
	    return "success";
	}
	else if (status=="Waiting"){
	    return "warning";
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

(function () {
   'use strict';

angular
    .module('loom.filters')
    .filter('statusColor', statusColor);

function statusColor(){
    return function(status){
	if (status=='Killed'){
	    return "default";
	}
	else if (status=='Failed'){
            return "danger";
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
}
}());

'use strict';

angular
    .module('loom.filters')
    .filter('parseId', parseId);

function parseId(){
    return function(input, component){
	if (input == null){
	    return;
	};
	var parts = input.split("@");
	if (parts.length < 2){
	    return;
	};
	if (component == 'name'){
	    return parts[0];
	};
	if (component == 'id'){
	    return parts[1];
	};
    };
};

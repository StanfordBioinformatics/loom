'use strict';

angular
    .module('loom.filters')
    .filter('flattenSteps', flattenSteps);

function recurseFlattenRun(run){
    if (!run.steps){
	return [run];
    };
    var steps = [].concat.apply([],run.steps.map(recurseFlattenRun));
    return [run].concat(steps);
};

function flattenSteps(){
    return function(run){
	if (!run.steps){return [];};
	var steps = recurseFlattenRun(run);
	steps.shift();
	return steps;
    };
};

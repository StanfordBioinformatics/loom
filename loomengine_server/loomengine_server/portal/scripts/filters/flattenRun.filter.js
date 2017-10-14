'use strict';

angular
    .module('loom.filters')
    .filter('flattenRun', flattenRun);

function recurseFlattenRun(run){
    if (run.steps){
	var steps = run.steps.map(function(step){
	    step.type='run';
	    step.level=run.level+1;
	    return step;
	});
	steps = steps.map(recurseFlattenRun);
	steps = [].concat.apply([],steps);
	return [run].concat(steps);
    }
    else if (run.tasks){
	var tasks = run.tasks.map(function(task){
	    task.type='task';
	    task.level=run.level+1;
	    return task;
	});
	tasks = tasks.map(recurseFlattenRun)
	tasks = [].concat.apply([],tasks);
	return [run].concat(tasks);
    }
    else if (run.all_task_attempts){
	var task_attempts = run.all_task_attempts.map(function(attempt){
	    attempt.type='task-attempt';
	    attempt.level=run.level+1;
	    return attempt;
	});
	return [run].concat(task_attempts);
    }
    else {
	return [run];
    };
};

function flattenRun(){
    return function(run){
	if (!run){return []};
	run.level = 0;
	var steps = recurseFlattenRun(run, 0);
	steps.shift();
	return steps;
    };
};

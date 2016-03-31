'use strict';

angular
    .module('loom.services')
    .service('DataService', DataService)

DataService.$inject = ['$http'];

function DataService($http) {
    /* Data is cached here so that it can be used by multiple scopes
       without extra queries to the server.

       Listens for stateChange and clears data to avoid having it go stale. */
    
    this.setActiveRun = setActiveRun;
    this.getActiveData = getActiveData;
    this.getRuns = getRuns;
	
    var activeData = {};
    
    function getActiveData() {
	return activeData;
    };

    function setActiveRun(runId) {
	return $http.get('/api/workflow_runs/' + runId)
            .then(function(response) {
		activeData.run = response.data;
		console.log(activeData.run);
            });
    };

    function getRuns() {
	return $http.get('/api/workflow_runs/')
	    .then(function(response) {
		return response.data.workflow_runs;
	    });
    };
};

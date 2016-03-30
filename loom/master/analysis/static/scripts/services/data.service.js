'use strict';

angular
    .module('loom.services')
    .factory('DataService', DataService)

DataService.$inject = ['$http', '$stateParams', '$state'];

function DataService($http, $stateParams, $state) {
    /* Data is cached here so that it can be used by multiple scopes
       without extra queries to the server.

       Listens for stateChange and clears data to avoid having it go stale. */
    
    var DataService = {
	getCurrentRun: getCurrentRun,
	getCurrentWorkflow: getCurrentWorkflow,
	getCurrentFile: getCurrentFile,
	getRunList: getRunList,
	getWorkflowList, getWorkflowList,
	getFileList, getFileList
    };
    
    return DataService;

    var currentRun = null;
    var currentWorkflow = null;
    var currentFile = null;
    
    var runs = {};
    var workflows = {};
    var files = {};
    
    function getCurrentRun() {
	console.log($stateParams);
	console.log($state);
	if (!currentRun && $stateParams.runId) {
	    $http.get('/api/workflow_runs/' + $stateParams.runId)
		.then(function(response) {
		    currentRun = response;
		});
	};
	return currentRun;
    };

    function getCurrentWorkflow() {};
    function getCurrentFile() {};
    function getRunList() {};
    function getWorkflowList() {};
    function getFileList() {};    
};

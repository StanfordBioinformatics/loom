'use strict';

angular
    .module('loom.services')
    .service('DataService', DataService)

DataService.$inject = ['$http'];

function DataService($http) {
    /* DataService retrieves and caches data from the server. */
    
    this.setActiveRun = setActiveRun;
    this.setActiveWorkflow = setActiveWorkflow;
    this.setActiveImportedFile = setActiveImportedFile;
    this.setActiveResultFile = setActiveResultFile;
    this.getActiveData = getActiveData;
    this.getRunRequests = getRunRequests;
    this.getWorkflows = getWorkflows;
    this.getImportedFiles = getImportedFiles;
    this.getResultFiles = getResultFiles;

    var activeData = {};
    
    function getActiveData() {
	return activeData;
    };

    function setActiveRun(runId) {
	return $http.get('/api/abstract-workflow-runs/' + runId + '/')
            .then(function(response) {
		activeData.run = response.data;
            });
    };

    function setActiveWorkflow(workflowId) {
	return $http.get('/api/abstract-workflows/' + workflowId + '/')
            .then(function(response) {
		activeData.workflow = response.data;
            });
    };

    function setActiveImportedFile(importedFileId) {
	return $http.get('/api/file-data-objects/' + importedFileId + '/')
            .then(function(response) {
		activeData.importedFile = response.data;
            });
    };

    function setActiveResultFile(resultFileId) {
	return $http.get('/api/file-data-objects/' + resultFileId + '/')
            .then(function(response) {
		activeData.resultFile = response.data;
            });
    };

    function getRunRequests() {
	return $http.get('/api/run-requests/')
	    .then(function(response) {
		return response.data.run_requests;
	    });
    };

    function getWorkflows() {
	return $http.get('/api/abstract-workflows/')
	    .then(function(response) {
		return response.data.abstract_workflows;
	    });
    };

    function getImportedFiles() {
	return $http.get('/api/imported-file-data-objects/')
	    .then(function(response) {
		return response.data.file_data_objects;
	    });
    };
    function getResultFiles() {
	return $http.get('/api/result-file-data-objects/')
	    .then(function(response) {
		return response.data.file_data_objects;
	    });
    };
};

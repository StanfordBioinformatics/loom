'use strict';

angular
    .module('loom.services')
    .service('DataService', DataService)

DataService.$inject = ['$http'];

function DataService($http) {
    /* DataService retrieves and caches data from the server. */
    
    this.setActiveStepRun = setActiveStepRun;
    this.setActiveWorkflow = setActiveWorkflow;
    this.setActiveStep = setActiveStep;
    this.setActiveRun = setActiveRun;
    this.setActiveImportedFile = setActiveImportedFile;
    this.setActiveResultFile = setActiveResultFile;
    this.getActiveData = getActiveData;
    this.getRuns = getRuns;    
    this.getWorkflows = getWorkflows;
    this.getImportedFiles = getImportedFiles;
    this.getResultFiles = getResultFiles;

    var activeData = {};
    
    function getActiveData() {
	return activeData;
    };

    function setActiveRun(runId) {
	return $http.get('/api/workflow-runs/' + runId + '/')
            .then(function(response) {
		activeData.run = response.data;
            });
    };

    function setActiveStepRun(stepRunId) {
	return $http.get('/api/step-runs/' + stepRunId + '/')
            .then(function(response) {
		activeData.stepRun = response.data;
            });
    };

    function setActiveWorkflow(workflowId) {
	return $http.get('/api/workflows/' + workflowId + '/')
            .then(function(response) {
		activeData.workflow = response.data;
            });
    };

    function setActiveStep(stepId) {
	return $http.get('/api/steps/' + stepId + '/')
            .then(function(response) {
		activeData.step = response.data;
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

    function setActiveFileSourceRuns(fileId) {
	return $http.get('/api/file-data-objects/' + fileId + '/source-runs/')
	    .then(function(response) {
		activeData.fileSourceRuns = response.data.runs;
	    });
    };

    function getRuns() {
	return $http.get('/api/workflow-runs/')
	    .then(function(response) {
		return response.data.workflow_runs;
	    });
    };

    function getWorkflows() {
	return $http.get('/api/workflows/')
	    .then(function(response) {
		return response.data.workflows;
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

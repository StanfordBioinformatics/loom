'use strict';

angular
    .module('loom.services')
    .service('DataService', DataService)

DataService.$inject = ['$http', '$q'];

function DataService($http, $q) {
    /* DataService retrieves and caches data from the server. */
    
    this.setActiveRun = setActiveRun;
    this.setActiveTemplate = setActiveTemplate;
    this.setActiveFile = setActiveFile;
    this.getAllActive = getAllActive;
    this.getRuns = getRuns;
    this.getTemplates = getTemplates;
    this.getImportedFiles = getImportedFiles;
    this.getResultFiles = getResultFiles;
    this.getLogFiles = getLogFiles;
    this.getFileProvenance = getFileProvenance;

    var activeData = {};
    
    function getAllActive() {
	return activeData;
    };

    function setActiveRun(runId) {
	return $http.get('/api/runs/' + runId + '/')
            .then(function(response) {
		activeData.run = response.data;
		if (response.data.task_runs) {
		    if (response.data.task_runs.length > 0) {
			return $http.get('/api/task-runs/' + activeData.run.task_runs[0].id + '/')
			    .then(function(response) {
				activeData.run.task_runs[0] = response.data;
			    });
		    };
		};
	    });
    };

    function setActiveTemplate(templateId) {
	return $http.get('/api/templates/' + templateId + '/')
            .then(function(response) {
		activeData.template = response.data;
            });
    };

    function setActiveFile(fileId) {
	return $http.get('/api/files/' + fileId + '/')
            .then(function(response) {
		activeData.file = response.data;
            });
    };

    function getFileProvenance(fileId) {
	return $http.get('/api/files/' + fileId + '/provenance/')
	    .then(function(response) {
		return response.data.provenance;
	    });
    };

    function getRuns() {
	return $http.get('/api/runs/')
	    .then(function(response) {
		return response.data;
	    });
    };

    function getTemplates() {
	return $http.get('/api/templates/')
	    .then(function(response) {
		return response.data;
	    });
    };

    function getImportedFiles() {
	return $http.get('/api/files/?source_type=imported')
	    .then(function(response) {
		return response.data;
	    });
    };
    function getResultFiles() {
	return $http.get('/api/files/?source_type=result')
	    .then(function(response) {
		return response.data;
	    });
    };
    function getLogFiles() {
	return $http.get('/api/files/?source_type=log')
	    .then(function(response) {
		return response.data;
	    });
    };
};

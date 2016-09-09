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
    this.getRunRequests = getRunRequests;
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
	return $http.get('/api/abstract-workflow-runs/' + runId + '/')
            .then(function(response) {
		activeData.run = response.data;
		if (response.data.task_runs) {
		    return $http.get('/api/task-runs/' + activeData.run.task_runs[0].id + '/')
			.then(function(response) {
			    activeData.run.task_runs[0] = response.data;
			});
		};
	    });
    };

    function setActiveTemplate(templateId) {
	return $http.get('/api/abstract-workflows/' + templateId + '/')
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

    function getRunRequests() {
	return $http.get('/api/run-requests/')
	    .then(function(response) {
		return response.data;
	    });
    };

    function getTemplates() {
	return $http.get('/api/imported-workflows/')
	    .then(function(response) {
		return response.data;
	    });
    };

    function getImportedFiles() {
	return $http.get('/api/imported-files/')
	    .then(function(response) {
		return response.data;
	    });
    };
    function getResultFiles() {
	return $http.get('/api/result-files/')
	    .then(function(response) {
		return response.data;
	    });
    };
    function getLogFiles() {
	return $http.get('/api/log-files/')
	    .then(function(response) {
		return response.data;
	    });
    };
};

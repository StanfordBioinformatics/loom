(function () {
   'use strict';

    angular
	.module("loom.services")
	.service("DataService", DataService)

    DataService.$inject = ["$http", "$q"];

    function DataService($http, $q) {
	/* DataService retrieves and caches data from the server. */

	this.setActiveRun = setActiveRun;
	this.setActiveTask = setActiveTask;
	this.setActiveTaskAttempt = setActiveTaskAttempt;
	this.setActiveTemplate = setActiveTemplate;
	this.setActiveFile = setActiveFile;
	this.getActiveData = getActiveData;
	this.getRuns = getRuns;
	this.getTemplates = getTemplates;
	this.getImportedFiles = getImportedFiles;
	this.getResultFiles = getResultFiles;
	this.getLogFiles = getLogFiles;
	this.getLoginAndVersionInfo = getLoginAndVersionInfo;

	var activeData = {};

	function getActiveData() {
            return activeData;
	}

	function setActiveRun(runId) {
	    activeData.focus = null
            return $http.get("/api/runs/" + runId + "/")
		.then(function(response) {
		    activeData.focus = response.data;
		});
	}

	function setActiveTask(taskId) {
	    activeData.focus = null
            return $http.get("/api/tasks/" + taskId + "/")
		.then(function(response) {
		    activeData.focus = response.data;
		});
	}

	function setActiveTaskAttempt(taskAttemptId) {
	    activeData.focus = null
            return $http.get("/api/task-attempts/" + taskAttemptId + "/")
		.then(function(response) {
		    activeData.focus = response.data;
		});
	}

	function setActiveTemplate(templateId) {
	    activeData.focus = null
            return $http.get("/api/templates/" + templateId + "/")
		.then(function(response) {
		    activeData.focus = response.data;
		});
	}

	function setActiveFile(fileId) {
	    activeData.focus = null
            return $http.get("/api/data-objects/" + fileId + "/")
		.then(function(response) {
		    activeData.focus = response.data;
		});
	}

	function getRuns(limit, offset) {
	    activeData.focus = null
            return $http.get("/api/runs/?parent_only&limit="+limit+"&offset="+offset)
		.then(function(response) {
		    return response.data;
		});
	}

	function getTemplates(limit, offset) {
	    activeData.focus = null
            return $http.get("/api/templates/?imported&limit="+limit+"&offset="+offset)
		.then(function(response) {
		    return response.data;
		});
	}

	function getImportedFiles(limit, offset) {
	    activeData.focus = null
            return $http.get("/api/data-objects/?source_type=imported&type=file&limit="+limit+"&offset="+offset)
		.then(function(response) {
		    return response.data;
		});
	}

	function getResultFiles(limit, offset) {
	    activeData.focus = null
            return $http.get("/api/data-objects/?source_type=result&type=file&limit="+limit+"&offset="+offset)
		.then(function(response) {
		    return response.data;
		});
	}

	function getLogFiles(limit, offset) {
	    activeData.focus = null
            return $http.get("/api/data-objects/?source_type=log&type=file&limit="+limit+"&offset="+offset)
		.then(function(response) {
		    return response.data;
		});
	}

	function getLoginAndVersionInfo() {
	    return $http.get("/api/info/")
		.then(function(response) {
		    activeData.username = response.data.username;
		    activeData.loginRequired = response.data.login_required;
		    activeData.version = response.data.version
		});
	}
    }
}());

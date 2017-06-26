"use strict";

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
    this.getAllActive = getAllActive;
    this.getRunSummary = getRunSummary;
    this.getRuns = getRuns;
    this.getTemplates = getTemplates;
    this.getImportedFiles = getImportedFiles;
    this.getResultFiles = getResultFiles;
    this.getLogFiles = getLogFiles;

    var activeData = {};

    function getAllActive() {
        return activeData;
    }

    function setActiveRun(runId) {
        return $http.get("/api/runs/" + runId + "/")
            .then(function(response) {
		activeData.run = response.data;
		expandRunInputsOutputs();
            });
    }

    function setActiveTask(taskId) {
        return $http.get("/api/tasks/" + taskId + "/")
            .then(function(response) {
		activeData.task = response.data;
            });
    }

    function setActiveTaskAttempt(taskAttemptId) {
        return $http.get("/api/task-attempts/" + taskAttemptId + "/")
            .then(function(response) {
		activeData.taskAttempt = response.data;
            });
    }

    function expandRunInputsOutputs() {
	if (activeData.run.inputs) {
            for (var i=0; i < activeData.run.inputs.length; i++) {
		expandRunInput(i);
            }
	}
	if (activeData.run.outputs) {
            for (var i=0; i < activeData.run.outputs.length; i++) {
		expandRunOutput(i);
            }
	}
    }

    function expandRunInput(i) {
        return $http.get("/api/data-nodes/"+activeData.run.inputs[i].data.uuid)
            .then(function(response) {
		activeData.run.inputs[i].data = response.data;
            });
    }

    function expandRunOutput(i) {
        return $http.get("/api/data-nodes/"+activeData.run.outputs[i].data.uuid)
            .then(function(response) {
		activeData.run.outputs[i].data = response.data;
            });
    }

    function setActiveTemplate(templateId) {
        return $http.get("/api/templates/" + templateId + "/")
            .then(function(response) {
		activeData.template = response.data;
		expandTemplateInputs();
            });
    }

    function expandTemplateInputs() {
	if (activeData.template.fixed_inputs) {
            for (var i=0; i < activeData.template.fixed_inputs.length; i++) {
		expandTemplateFixedInput(i);
            }
	}
    }

    function expandTemplateFixedInput(i) {
        return $http.get("/api/data-nodes/"+activeData.template.fixed_inputs[i].data.uuid)
            .then(function(response) {
		activeData.template.fixed_inputs[i].data = response.data;
            });
    }

    function setActiveFile(fileId) {
        return $http.get("/api/data-objects/" + fileId + "/")
            .then(function(response) {
		activeData.file = response.data;
            });
    }

    function getRunSummary(runId) {
	return $http.get("/api/runs/" + runId + "/?summary")
	    .then(function(response) {
		return response.data;
	    });
    }
    function getRuns() {
        return $http.get("/api/runs/?parent_only")
            .then(function(response) {
		return response.data;
            });
    }

    function getTemplates() {
        return $http.get("/api/templates/?imported")
            .then(function(response) {
		return response.data;
            });
    }

    function getImportedFiles() {
        return $http.get("/api/data-objects/?source_type=imported&type=file")
            .then(function(response) {
		return response.data;
            });
    }

    function getResultFiles() {
        return $http.get("/api/data-objects/?source_type=result&type=file")
            .then(function(response) {
		return response.data;
            });
    }

    function getLogFiles() {
        return $http.get("/api/data-objects/?source_type=log&type=file")
            .then(function(response) {
		return response.data;
            });
    }
}

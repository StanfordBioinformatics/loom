'use strict';

angular
    .module('loom.routes')
    .config(config);

config.$inject = ['$routeProvider'];

function config($routeProvider) {

    $routeProvider
        .when('/runs/:runId/steps/:stepRunId', {
            templateUrl: 'views/step-run-detail.html',
            controller: 'StepRunDetailController'
        })
        .when('/runs/:runId', {
            templateUrl: 'views/run-detail.html',
            controller: 'RunDetailController'
        })
        .when('/runs', {
            templateUrl: 'views/run-list.html',
            controller: 'RunListController'
        })
        .when('/workflows', {
            templateUrl: 'views/workflow-list.html',
            controller: 'WorkflowListController'
        })
        .when('/workflows/:workflowId', {
            templateUrl: 'views/workflow-detail.html',
            controller: 'WorkflowDetailController'
        })
        .when('/workflows/:workflowId/steps/:stepId', {
            url: '/steps/{stepId}',
            templateUrl: 'views/step-detail.html',
            controller: 'StepDetailController'
        })
        .when('/result-files', {
            templateUrl: 'views/result-file-list.html',
            controller: 'ResultFileListController'
        })
        .when('/imported-files', {
            templateUrl: 'views/imported-file-list.html',
            controller: 'ImportedFileListController'
        })
        .when('/imported-files/:importedFileId', {
            templateUrl: 'views/imported-file-detail.html',
            controller: 'ImportedFileDetailController'
        })
        .when('/result-files/:resultFileId', {
            templateUrl: 'views/result-file-detail.html',
            controller: 'ResultFileDetailController'
        })
	.otherwise('/runs');
};

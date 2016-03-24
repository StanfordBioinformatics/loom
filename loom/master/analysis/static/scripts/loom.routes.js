'use strict';

angular
    .module('loom.routes')
    .config(config);

config.$inject = ['$stateProvider', '$urlRouterProvider'];

function config($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/runs');

    $stateProvider
        .state('runs', {
            url: '/runs',
            templateUrl: 'partials/run-list.html',
            controller: 'RunListController'
        })
        .state('runs.run', {
            url: '/{workflowRunId}',
            templateUrl: 'partials/run-detail.html',
            controller: 'RunDetailController'
        })
        .state('runs.run.step', {
            url: '/{stepId}', 
            templateUrl: 'partials/run-step-detail.html',
            controller: 'RunStepDetailController'
        })
        .state('workflows', {
            url: '/workflows',
            templateUrl: 'partials/workflow-list.html',
            controller: 'WorkflowListController'
        })
        .state('workflows.workflow', {
            url: '/{workflowId}',
            templateUrl: 'partials/workflow-detail.html',
            controller: 'WorkflowDetailController'
        })
        .state('workflows.workflow.step', {
            url: '/steps/{stepId}',
            templateUrl: 'partials/workflow-step-detail.html',
            controller: 'WorkflowStepDetailController'
        })
        .state('files', {
            url:'/files', 
            templateUrl: 'partials/file-list.html',
            controller: 'FileListController'
        })
        .state('files.file', {
            url:'/{fileId}', 
            templateUrl: 'partials/file-detail.html',
            controller: 'FileDetailController'
        });
};

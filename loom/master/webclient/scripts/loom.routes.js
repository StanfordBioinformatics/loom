'use strict';

angular
    .module('loom.routes')
    .config(config);

config.$inject = ['$routeProvider'];

function config($routeProvider) {

    $routeProvider
        .when('/runs', {
            templateUrl: 'views/run-list.html',
            controller: 'RunListController'
        })
        .when('/runs/:runId', {
            templateUrl: 'views/run-detail.html',
            controller: 'RunDetailController'
        })

        .when('/workflows', {
            templateUrl: 'views/workflow-list.html',
            controller: 'WorkflowListController'
        })
        .when('/workflows/:workflowId', {
            templateUrl: 'views/workflow-detail.html',
            controller: 'WorkflowDetailController'
        })
        .when('/result-files', {
            templateUrl: 'views/result-file-list.html',
            controller: 'ResultFileListController'
        })
        .when('/imported-files', {
            templateUrl: 'views/imported-file-list.html',
            controller: 'ImportedFileListController'
        })
        .when('/data/:dataId', {
            templateUrl: 'views/data-detail.html',
            controller: 'DataDetailController'
        })
	.otherwise('/runs');
};

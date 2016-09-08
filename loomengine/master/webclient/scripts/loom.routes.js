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

        .when('/templates', {
            templateUrl: 'views/template-list.html',
            controller: 'TemplateListController'
        })
        .when('/templates/:templateId', {
            templateUrl: 'views/template-detail.html',
            controller: 'TemplateDetailController'
        })
        .when('/files/imported', {
            templateUrl: 'views/file-list.html',
            controller: 'ImportedFileListController'
        })
        .when('/files/results', {
            templateUrl: 'views/file-list.html',
            controller: 'ResultFileListController'
        })
        .when('/files/logs', {
            templateUrl: 'views/file-list.html',
            controller: 'LogFileListController'
        })
    	.when('/files', {redirectTo: '/files/imported'})
        .when('/files/:fileId', {
            templateUrl: 'views/file-detail.html',
            controller: 'FileDetailController'
        })
        .when('/files/:fileId/provenance', {
            templateUrl: 'views/file-provenance.html',
            controller: 'FileProvenanceController'
        })
	.otherwise('/runs');
};

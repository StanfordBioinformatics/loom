(function () {
   'use strict';

angular
    .module('loom.routes')
    .config(config);

config.$inject = ['$routeProvider'];

function config($routeProvider) {

    $routeProvider
        .when('/login', {
            templateUrl: 'views/login.html',
            controller: 'AuthController'
        })
        .when('/runs', {
            templateUrl: 'views/run-list.html',
            controller: 'RunListController'
        })
        .when('/runs/:runId', {
            templateUrl: 'views/run-detail.html',
            controller: 'RunDetailController'
        })
        .when('/tasks/:taskId', {
            templateUrl: 'views/task-detail.html',
            controller: 'TaskDetailController'
        })
        .when('/task-attempts/:taskAttemptId', {
            templateUrl: 'views/task-attempt-detail.html',
            controller: 'TaskAttemptDetailController'
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
	.otherwise('/runs');
};

}());

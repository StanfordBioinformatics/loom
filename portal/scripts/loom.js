(function () {
   'use strict';

    var loom = angular
	.module('loom', [
	    'loom.controllers',
	    'loom.directives',
	    'loom.filters',
	    'loom.routes',
	    'loom.services',
	    'bw.paging',
	])
	.config(['$locationProvider', function($locationProvider) {
	    $locationProvider.html5Mode(false);
	    $locationProvider.hashPrefix('');
	}])
	.config(function ($httpProvider) {
	    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
	    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
            $httpProvider.interceptors.push('responseObserver');
	})
	.config(function ($provide) {
	    $provide.factory('responseObserver', responseObserver);
	    function responseObserver($q, $window) {
		return {
		    'responseError': function(errorResponse) {
			switch (errorResponse.status) {
			case 403:
			    $window.location = '#/login';
			    break;
			case 500:
			    $window.location = './500.html';
			    break;
			}
			return $q.reject(errorResponse);
		    }
		}
	    }
	});

    angular
	.module('loom.controllers', ['loom.services', 'ngResource']);

    angular
	.module('loom.directives', []);

    angular
	.module('loom.filters', []);

    angular
	.module('loom.routes', ['ngRoute']);

    angular
	.module('loom.services', []);

}());

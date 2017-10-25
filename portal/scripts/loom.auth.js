(function (){
    'use strict';

    angular.module('loom.auth', ['ngResource']).
	config(['$httpProvider', function($httpProvider){
            // django and angular both support csrf tokens. This tells
            // angular which cookie to add to what header.
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
	}]).
	factory('api', function($resource){
            // defining the endpoints. Note we escape url trailing dashes: Angular
            // strips unescaped trailing slashes. Problem as Django redirects urls
            // not ending in slashes to url that ends in slash for SEO reasons, unless
            // we tell Django not to [3]. This is a problem as the POST data cannot
            // be sent with the redirect. So we want Angular to not strip the slashes!
	    return {
		auth: $resource('/api/auth\\/', {}, {
                    logout: {method: 'DELETE'}
		}),
		users: $resource('/api/users\\/', {}, {
                    create: {method: 'POST'}
		})
            };
	}).
	controller('AuthController', function($scope, $resource, $window, api) {
            // Angular does not detect auto-fill or auto-complete. If the browser
            // autofills "username", Angular will be unaware of this and think
            // the $scope.username is blank. To workaround this we use the
            // autofill-event polyfill [4][5]
            $('#id_auth_form input').checkAndTriggerAutoFillEvent();
	    
            $scope.getCredentials = function(){
		return {username: $scope.username, password: $scope.password};
            };
	    
	    function get_auth_header(data){
		// as per HTTP authentication spec [1], credentials must be
		// encoded in base64. Lets use window.btoa [2]
		return 'Basic ' + btoa(data.username + ':' + data.password);
            }

            $scope.login = function(){
		function get_login_resource(credentials) {
		    return $resource('/api/auth\\/', {}, {
			login: {method: 'POST', headers: {
			    'Authorization': get_auth_header(credentials)
			}}
		    })
		};
		get_login_resource($scope.getCredentials()).login()
		    .$promise
                    .then(function(data){
			// on good username and password
			$scope.logged_in_as = data.username;
			$window.location = '#/runs';
                    })
                    .catch(function(data){
			// on incorrect username and password
			alert(data.data.detail);
                    });
            };

            $scope.logout = function(){
		api.auth.logout()
		    .$promise
		    .then(function(){
			$scope.logged_in_as = undefined;
			$window.location = '#/login';
		    });
            };
            $scope.register = function($event){
		// prevent login form from firing
		$event.preventDefault();
		// create user and immediatly login on success
		api.users.create($scope.getCredentials()).
                    $promise
                    .then($scope.login)
                    .catch(function(data){
                        alert(data.data.username);
                    });
            };
	});

// [1] https://tools.ietf.org/html/rfc2617
// [2] https://developer.mozilla.org/en-US/docs/Web/API/Window.btoa
// [3] https://docs.djangoproject.com/en/dev/ref/settings/#append-slash
// [4] https://github.com/tbosch/autofill-event
// [5] http://remysharp.com/2010/10/08/what-is-a-polyfill/

// https://richardtier.com/2014/03/15/authenticate-using-django-rest-framework-endpoint-and-angularjs/

}());

'use strict';

angular
    .module('loom', [
	'loom.controllers',
	'loom.directives',
	'loom.filters',
	'loom.routes',
	'loom.services',
    ]);

angular
    .module('loom.controllers', ['loom.services']);

angular
    .module('loom.directives', []);

angular
    .module('loom.filters', []);

angular
    .module('loom.routes', ['ngRoute']);

angular
    .module('loom.services', []);

'use strict';

angular
    .module('loom.services')
    .factory('Data', Data)

Data.$inject = [];

function Data() {
	var DataServiceScope = {};
	return DataServiceScope;
    };

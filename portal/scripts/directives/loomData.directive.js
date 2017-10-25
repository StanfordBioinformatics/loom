(function () {
   'use strict';

angular
    .module('loom.directives')
    .directive('loomData', loomData)

function loomData($compile){
    return {
	restrict: "E",
	replace: true,
	scope: {
	    contents: '='
	},
	template: "<span><a ng-if='contents.type==\"file\"' href='#/files/{{contents.uuid}}'>{{contents.value.filename}}@{{contents.uuid|limitTo:8}}</a>{{contents.type != 'file' ? contents.value : null}}<ul ng-if='contents.value==null'><li ng-repeat='child in contents'>&nbsp;<loom-data contents='child'></loom-data></li><ul></span>"
    }
}
}());

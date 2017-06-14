'use strict';

angular
    .module('loom.directives')
    .directive('collapseAll', collapseAll)

function collapseAll() {
    return {
	restrict: 'C',
	scope: {
	    val: '='
	},
        link: function(scope, element, attrs) {
            element.bind('click', function() {
		var elements = document.getElementsByClassName("collapse");
		for (let c of elements) {
		    c.classList.remove("in");
		}
		var buttons = document.querySelectorAll("[aria-expanded]")
		for (let b of buttons) {
		    b.setAttribute("aria-expanded", "false");
		}
            });
	}
    }
}

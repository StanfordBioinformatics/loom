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
		for (var i = 0; i < elements.length; i++) {
		    elements[i].classList.remove("in");
		}
		var buttons = document.querySelectorAll("[aria-expanded]")
		for (var i = 0; i < buttons.length; i++) {
		    buttons[i].setAttribute("aria-expanded", "false");
		}
            });
	}
    }
}

'use strict';

angular
    .module('loom.directives')
    .directive('provenanceGraph', provenanceGraph)

function provenanceGraph() {
    return {
	restrict: 'E',
	scope: {
	    val: '='
	},
	link: linkFunction,
    };
};

var svg,
    inner;

function linkFunction(scope, element, attrs) {

    scope.$watch('val', changeFunction);
    
    // Create svg and g(raph) elements
    var margin = 20,
	width = 960;

    svg = d3.select(element[0])
        .append("svg")
        .attr("width", width);
    inner = svg.append("g");
};

function changeFunction (newVal, oldVal) {

    console.log(newVal.fileId);
    
    // Create a new directed graph
    var g = new dagreD3.graphlib.Graph().setGraph({});

    var files = [
	{id: "1"},
	{id: "2"},
	{id: "3",
	 task: "a"},
	{id: "4",
	 task: "b"},
	{id: "5",
	 task: "c"}
    ];

    var tasks = [
	{id: "a",
	 inputs: ["1"]},
	{id: "b",
	 inputs: ["2"]},
	{id: "c",
	 inputs: ["3", "4"]}
    ];

    // Automatically label each of the nodes
    files.forEach(function(file) { g.setNode(file.id, { label: file.id, shape: "diamond" }); g.node(file.id).style = "fill: #f99; stroke: #000"; });
    tasks.forEach(function(task) { g.setNode(task.id, { label: task.id, shape: "ellipse" }); g.node(task.id).style = "fill: #8bf; stroke: #000"; });

    files.forEach(
	function(file) {
	    if (file.task) {
		g.setEdge(file.task, file.id, {});
	    };
	}
    );

    tasks.forEach(
	function(task) {
	    if (task.inputs) {
		task.inputs.forEach(
		    function(input){
			g.setEdge(input, task.id, {});
		    }
		);
	    };
	}
    );

    // Set up zoom support
    var zoom = d3.behavior.zoom().on("zoom", function() {
	inner.attr("transform", "translate(" + d3.event.translate + ")" +
		   "scale(" + d3.event.scale + ")");
    });
    svg.call(zoom);

    // Create the renderer
    var render = new dagreD3.render();

    console.log(inner);
    console.log(g);
    
    // Run the renderer. This is what draws the final graph.
    render(inner, g);

    // Center the graph
    var initialScale = 0.75;
    zoom
	.translate([(svg.attr("width") - g.graph().width * initialScale) / 2, 20])
	.scale(initialScale)
	.event(svg);
    svg.attr('height', g.graph().height * initialScale + 40);

};

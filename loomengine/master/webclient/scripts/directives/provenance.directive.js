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

    if (!newVal) {
	return;
    }

    var files = newVal.files
    var tasks = newVal.tasks
    var edges = newVal.edges
    
    // Create a new directed graph
    var g = new dagreD3.graphlib.Graph().setGraph({});

    // Automatically label each of the nodes
    files.forEach(function(file) { g.setNode(file.id, { label: file.file_content.filename, shape: "diamond" }); g.node(file.id).style = "fill: #f99; stroke: #000"; });
    tasks.forEach(function(task) { g.setNode(task.id, { label: task.name, shape: "ellipse" }); g.node(task.id).style = "fill: #8bf; stroke: #000"; });
    edges.forEach(function(edge) { g.setEdge(edge[0], edge[1], {}); });

    // Set up zoom support
    var zoom = d3.behavior.zoom().on("zoom", function() {
	inner.attr("transform", "translate(" + d3.event.translate + ")" +
		   "scale(" + d3.event.scale + ")");
    });
    svg.call(zoom);

    // Create the renderer
    var render = new dagreD3.render();

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

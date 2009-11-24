/*global $, document, p: true, Processing, top, window */
/*jslint white: false, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
"use strict";
var edge_list = [], nodes = [], NODES, EDGES, SIZE, NEW_RADIUS,
    DOUBLECLICK, LIVE, SPRING, FIXED_LENGTH,
    selected_node, dragged_node, dragging_flag, last_click_time,
    initial_x, initial_y

var edges = [], num_vertices = null, pos = null;

NODES = 10;
EDGES = 20;
SIZE = 350;
NEW_RADIUS = 20;
DOUBLECLICK = 250;
LIVE = false;
SPRING = 0.999;
FIXED_LENGTH = 100.0;

function rand(a, b) {
    return a + Math.floor(Math.random() * (b - a));
}

function Node(x, y) {
    this.x = x;
    this.y = y;
    this.size = 7;
}

Node.prototype.display = function () {
    p.stroke(0);
    if (this.selected) {
	p.fill(255, 0, 0);
	p.ellipse(this.x, this.y, this.size, this.size);
    } else {
	p.fill(0);
	p.ellipse(this.x, this.y, this.size, this.size);
    }
};

Node.prototype.distance_to = function (x, y) {
    return Math.sqrt(Math.pow((x - this.x), 2) + Math.pow((y - this.y), 2));
};

Node.prototype.is_hit = function (x, y) {
    return Math.abs(x - this.x) < this.size &&
	Math.abs(y - this.y) < this.size;
};

function Edge(node1, node2) {
    this.node1 = node1;
    this.node2 = node2;
}

Edge.prototype.shrink = function () {
    var d, gx, gy, mx, my;

    mx = (this.node1.x + this.node2.x) / 2;
    my = (this.node1.y + this.node2.y) / 2;

    if (this.node1 !== dragged_node) {
	d = this.node1.distance_to(mx, my);
	gx = mx + (this.node1.x - mx) / d * FIXED_LENGTH / 2;
	gy = my + (this.node1.y - my) / d * FIXED_LENGTH / 2;
	this.node1.x = gx + (this.node1.x - gx) * SPRING;
	this.node1.y = gy + (this.node1.y - gy) * SPRING;
    }
    if (this.node2 !== dragged_node) {
	d = this.node2.distance_to(mx, my);
	gx = mx + (this.node2.x - mx) / d * FIXED_LENGTH / 2;
	gy = my + (this.node2.y - my) / d * FIXED_LENGTH / 2;
	this.node2.x = gx + (this.node2.x - gx) * SPRING;
	this.node2.y = gy + (this.node2.y - gy) * SPRING;
    }
};

Edge.prototype.display = function () {
    if (this.node1.x > SIZE || this.node1.y > SIZE ||
	this.node1.x < 0 || this.node1.y < 0 ||
	this.node2.x > SIZE || this.node2.y > SIZE ||
	this.node2.x < 0 || this.node2.y < 0) {
	p.stroke(255, 0, 0);
    } else {
	if (this.node1.selected || this.node2.selected) {
	    p.stroke(0, 0, 200);
	} else {
	    p.stroke(0);
	}
    }
    p.line(this.node1.x, this.node1.y, this.node2.x, this.node2.y);
};

function add_node(node) {
    if (nodes.indexOf(node) === -1) {
	nodes.push(node);
    }
}

function remove_node(node) {
    var edge, i, index;
    for (i = edge_list.length - 1; i > -1; i -= 1) {
	edge = edge_list[i];
	if (edge.node1 === node || edge.node2 === node) {
	    edge_list.splice(i, 1);
	}
    }
    index = nodes.indexOf(node);
    if (index !== -1) {
	nodes.splice(index, 1);
    }
}

function add_edge_between_nodes(node1, node2) {
    if (node1 === node2) {
	// Only simple graphs are implemented so far.
	return;
    }
    edge_list.push(new Edge(node1, node2));
    if (nodes.indexOf(node1) === -1) {
	nodes.add(node1);
    }
    if (nodes.indexOf(node2) === -1) {
	nodes.add(node2);
    }
}

function toggle_edge(node1, node2) {
    var edge, existing = false, i, new_edge;
    if (node1 === node2) {
	// Only simple graphs are implemented so far.
	return;
    }
    new_edge = new Edge(node1, node2);
    for (i = edge_list.length - 1; i > -1; i -= 1) {
	edge = edge_list[i];
	if ((edge.node1 === new_edge.node1 && edge.node2 === new_edge.node2) ||
	    (edge.node1 === new_edge.node2 && edge.node2 === new_edge.node1)) {
	    existing = true;
	    break;
	}
    }
    if (existing) {
	edge_list.splice(i, 1);
    } else {
	edge_list.push(new_edge);
    }
}

function set_graph() {
    var i, n1, n2;

    if (!pos) {
	for (i = 0; i < NODES; i += 1) {
	    add_node(new Node(rand(0, SIZE), rand(0, SIZE)));
	}
	for (i = 0; i < EDGES; i += 1) {
	    n1 = rand(0, NODES);
	    n2 = rand(0, NODES);
	    add_edge_between_nodes(nodes[n1], nodes[n2]);
	}
    }
    for (i = 0; i < num_vertices; i += 1) {
	if (pos) {
	    add_node(new Node(pos[i][0] * 8 * SIZE / 10 + SIZE / 10,
			      pos[i][1] * 8 * SIZE / 10 + SIZE / 10));
	} else {
	    add_node(new Node(rand(0, SIZE), rand(0, SIZE)));
	}
    }
    for (i = 0; i < edges.length; i += 1) {
	add_edge_between_nodes(nodes[edges[i][0]], nodes[edges[i][1]]);
    }
    p.draw();
}

function display_graph() {
    var i;
    for (i = 0; i < edge_list.length; i += 1) {
	edge_list[i].display();
	if (LIVE) {
	    edge_list[i].shrink();
	}
    }
    for (i = 0; i < nodes.length; i += 1) {
	nodes[i].display();
    }
}

function setup() {
    p.size(SIZE, SIZE);
    set_graph();
    p.rectMode(p.RADIUS);
    p.ellipseMode(p.RADIUS);
    p.noLoop();
}

function update_sliders() {
    SPRING = (1 - 1e-2) + 1e-4 * (100 - $('#val_edge').val());
    FIXED_LENGTH = $('#val_fixed_length').val();
}

function draw() {
    update_sliders();
    p.background(255);
    display_graph();
}

function toggle_live() {
    if (LIVE) {
	LIVE = false;
	p.noLoop();
    } else {
	LIVE = true;
	p.loop();
    }
}

function mousePressed() {
    var clicked_node, closest_distance, i, new_distance;
    if (!LIVE) {
	p.loop();
    }
    for (i = 0; i < nodes.length; i += 1) {
	if (nodes[i].is_hit(p.mouseX, p.mouseY)) {
	    clicked_node = nodes[i];
	    break;
	}
    }
    if (!clicked_node) {
	closest_distance = SIZE;
	for (i = 0; i < nodes.length; i += 1) {
	    new_distance = nodes[i].distance_to(p.mouseX, p.mouseY);
	    if (new_distance < closest_distance) {
		closest_distance = new_distance;
	    }
	}
	if (closest_distance > NEW_RADIUS) {
	    add_node(new Node(p.mouseX, p.mouseY));
	}
	return;
    } else {
	dragged_node = clicked_node;
	initial_x = dragged_node.x;
	initial_y = dragged_node.y;
    }
}

function mouseDragged() {
    if (dragged_node) {
	dragging_flag = true;
	dragged_node.x = p.mouseX;
	dragged_node.y = p.mouseY;
    }
}

function mouseReleased() {
    if (dragged_node) {
	if (dragging_flag) {
	    dragging_flag = false;
	    if (dragged_node.x > SIZE || dragged_node.y > SIZE ||
		dragged_node.x < 0 || dragged_node.y < 0) {
		remove_node(dragged_node);
		if (selected_node === dragged_node) {
		    selected_node = false;
		}
		dragged_node = false;
	    }
	} else {
	    if (p.millis() - last_click_time < DOUBLECLICK) {
		remove_node(dragged_node);
		if (selected_node === dragged_node) {
		    selected_node = false;
		}
	    } else if (selected_node) {
		toggle_edge(selected_node, dragged_node);
		if (!p.keyPressed) {
		    selected_node.selected = false;
		    selected_node = false;
		} else {
		    if (selected_node === dragged_node) {
			selected_node.selected = false;
			selected_node = false;
		    }
		}
	    } else {
		selected_node = dragged_node;
		selected_node.selected = true;
	    }
	}
	dragged_node = false;
	last_click_time = p.millis();
	p.redraw();
    }
    if (!LIVE) {
	p.noLoop();
    }
}

function mouse_out() {
    if (dragged_node) {
	dragged_node.x = initial_x;
	dragged_node.y = initial_y;
	dragged_node = false;
    }
}

function positions_dict() {
    var i, out;
    out = "{";
    for (i = 0; i < nodes.length; i += 1) {
	out += i + ":[" + nodes[i].x + "," + (SIZE - nodes[i].y) + "],";
    }
    return out.substring(0, out.length - 1) + "}";
}

function adjacency_lists_dict() {
    var edge, empty, i, j, node, out;
    out = "{";
    for (i = 0; i < nodes.length; i += 1) {
	out += i + ":[";
	node = nodes[i];
	empty = true;
	for (j = 0; j < edge_list.length; j += 1) {
	    edge = edge_list[j];
	    if (edge.node1 === node) {
		if (!empty) {
		    out += ",";
		}
		empty = false;
		out += nodes.indexOf(edge.node2);
	    }
	    if (edge.node2 === node) {
		if (!empty) {
		    out+=",";
		}
		empty = false;
		out += nodes.indexOf(edge.node1);
	    }
	}
	out += "],";
    }
    return out.substring(0, out.length - 1) + "}";
}

function update_sage() {
    return [adjacency_lists_dict(), positions_dict(), $('#graph_name').val()];
}


$(document).ready(function () {
    var cell_id, cell_outer, loc;

    // Retrieve graph data and name from parent document.
    loc = window.location.href;
    cell_id = parseInt(loc.slice(loc.search('cell_id=') + 8), 10);
    cell_outer = $('#cell_outer_' + cell_id, top.document);
    eval($('#graph_data_' + cell_id, cell_outer).val());
    $('#graph_name').val($('#graph_name_' + cell_id, cell_outer).val());

    // Set up processing.js.
    p = Processing($('#canvas')[0], '');
    p.setup = setup;
    p.draw = draw;
    p.mouseDragged = mouseDragged;
    p.mousePressed = mousePressed;
    p.mouseReleased = mouseReleased;
    p.init();

    $('#help').hide();

    $('#help_button').click(function () {
	$('#help').toggle();
    });

    $('#live').click(function() {
	toggle_live();
    });

    $('#slider_edge').slider({
	min: 0,
	max: 100,
	value: 50,
	slide: function(event, ui) {
	    $('#val_edge').val(ui.value);
	}
    });

    $('#slider_fixed_length').slider({
	min: 0,
	max: 200,
	value: 100,
	slide: function(event, ui) {
	    $('#val_fixed_length').val(ui.value);
	}
    });
});

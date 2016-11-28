function is_ship(obj) {
    return 'controller' in obj;
}
function is_pellet(obj) {
    return 'time_to_live' in obj;
}

function draw_planet(ctx, body) {
    var p = body.state.position;
    ctx.fillStyle = '#68c';
    ctx.beginPath();
    ctx.arc(p.x, p.y, body.radius, 0, 2 * Math.PI);
    ctx.fill();
}

function draw_ship(ctx, body, color) {
    // Constants
    var alpha = Math.PI / 4;
    var bigger_by = 1.2;  // inflate the radius to 'match it up'

    // Compute vertices & draw
    var p = body.state.position;
    var a0 = body.state.orientation;
    var a1 = a0 + Math.PI - alpha;
    var a2 = a0 + Math.PI + alpha;
    var r = bigger_by * body.radius;
    ctx.strokeStyle = color;
    ctx.lineWidth = 0.5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(p.x + r * Math.sin(a0), p.y + r * Math.cos(a0));
    ctx.lineTo(p.x + r * Math.sin(a1), p.y + r * Math.cos(a1));
    ctx.lineTo(p.x + r * Math.sin(a2), p.y + r * Math.cos(a2));
    ctx.lineTo(p.x + r * Math.sin(a0), p.y + r * Math.cos(a0));
    ctx.stroke();
}

function draw_pellet(ctx, body, space_dimensions) {
    var size_ratio = 0.02;
    var size = size_ratio * Math.min(space_dimensions.x, space_dimensions.y);
    var p = body.state.position;
    var a = body.state.orientation;
    var ax = 0.5 * size * Math.sin(a);
    var ay = 0.5 * size * Math.cos(a);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = size / 4;
    ctx.beginPath();
    ctx.moveTo(p.x - ax, p.y - ay);
    ctx.lineTo(p.x + ax, p.y + ay);
    ctx.stroke();
}

function draw(space_dimensions, objects, ship_colors) {
    var canvas = $('.player-canvas')[0];
    var ctx = canvas.getContext('2d');

    // The content should be centered and top aligned
    // - also flip y so that it runs up from the bottom
    var scale = Math.min(canvas.width / space_dimensions.x,
                         canvas.height / space_dimensions.y);
    ctx.resetTransform();
    ctx.translate(0.5 * (canvas.width - scale * space_dimensions.x),
                  canvas.height);
    ctx.scale(scale, -scale);

    // Clip to the dimensions of space, and fill it in
    ctx.beginPath();
    ctx.rect(0, 0, space_dimensions.x, space_dimensions.y);
    ctx.clip();
    ctx.fillStyle = '#000';
    ctx.fill();

    // Draw all the objects
    Object.keys(objects).forEach(function(id) {
	var obj = objects[id];
	if (is_ship(obj)) {
	    draw_ship(ctx, obj.body, ship_colors[id]);
	} else if (is_pellet(obj)) {
	    draw_pellet(ctx, obj.body, space_dimensions);
	} else {
	    draw_planet(ctx, obj.body);
	}
    });
}

/* Generates color codes to assign to ships. */
function ship_palette() {
    var colors = ['#f00', '#0f0', '#22f'];
    var index = -1;
    return function () {
	index = (index + 1) % colors.length;
	return colors[index];
    };
}

function log_loaded(log) {
    // State
    var space_dimensions = log[0].data.dimensions;
    var objects = {};
    var ship_colors = {};
    var gen_ship_color = ship_palette();
    var event = 1;
    var callback_id;

    function step() {
	// Update the game objects
	var step_data = log[event].data;
	step_data.forEach(function (e) {
	    if (e.id in objects) {
		var obj = objects[e.id];
		if (Object.keys(e.data).length == 0) {
		    delete objects[e.id];
		} else {
		    obj.body.state = e.data.body;
		    if (is_ship(obj)) {
			obj.weapon.state = e.data.weapon;
			obj.controller.state = e.data.controller;
		    } else if (is_pellet(obj)) {
			obj.time_to_live = e.data.time_to_live;
		    } else {
			// Planet has no other updatable state
		    }
		}
	    } else {
		// Should be {Planet, Ship, Pellet}.Create
                objects[e.id] = e.data;
		if (is_ship(e.data) && !(e.id in ship_colors)) {
		    ship_colors[e.id] = gen_ship_color();
		}
	    }
	});
	// Draw the current state
	draw(space_dimensions, objects, ship_colors);

	// Advance
	event = event + 1;
	if (log.length <= event) {
	    window.clearInterval(callback_id);
	}
    }

    callback_id = window.setInterval(step, 10);
}

$(function() {
    var id = 'sample';  // TODO

    $.get({url: '/replay/' + id,
           cache: false
          }).then(log_loaded);
});

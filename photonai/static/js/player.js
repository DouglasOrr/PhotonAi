var settings = {
    canvas_aspect: 2./3,
    tick_time: 10 // ms
};

// -------------------- Rendering --------------------

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
    ctx.lineWidth = 2 / scale;
    ctx.strokeStyle = '#a44';
    ctx.stroke();

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

// Generates color codes to assign to ships.
function ship_palette() {
    var colors = ['#f00', '#0f0', '#22f'];
    var index = -1;
    return function () {
	index = (index + 1) % colors.length;
	return colors[index];
    };
}

var state = {
    playing: false,
    n: 0,
    space_dimensions: null,
    states: null,
    ship_colors: null
}

function redraw() {
    // Draw the current state
    draw(state.space_dimensions,
	 state.states[state.n],
	 state.ship_colors);
}

function refresh_playing() {
    if (state.playing) {
	$('.player-play').hide();
	$('.player-restart').hide();
	$('.player-pause').show();

    } else {
	$('.player-pause').hide();
	if (state.states !== null &&
	    state.n == state.states.length - 1) {
	    $('.player-play').hide();
	    $('.player-restart').show();
	} else {
	    $('.player-restart').hide();
	    $('.player-play').show();
	}
    }
}

function set_playing(playing) {
    state.playing = playing && state.states !== null;
    refresh_playing();
}

function tick() {
    if (state.playing) {
	$('.player-seek').val(state.n);
	redraw();
	if (state.n < state.states.length - 1) {
	    state.n += 1;
	} else {
	    set_playing(false);
	}
    }
}

function seek(n) {
    if (state.states !== null) {
	if (n < 0) {
	    n = state.states.length + n;
	}
	$('.player-seek').val(n);
	state.n = n;
	refresh_playing();
	redraw();
    }
}

function setup_log(log) {
    state.space_dimensions = log[0].data.dimensions;
    state.n = 0;
    state.states = [];
    state.ship_colors = {};

    var gen_ship_color = ship_palette();
    var objects = {};
    log.slice(1).forEach(function (step) {
	// Copy in case we modify
	objects = $.extend({}, objects);
	step.data.forEach(function (e) {
	    if (e.id in objects) {
		if (Object.keys(e.data).length == 0) {
		    delete objects[e.id];
		} else {
		    var obj = $.extend({}, objects[e.id]);
		    obj.body = $.extend({}, obj.body);
		    obj.body.state = e.data.body;
		    if (is_ship(obj)) {
			obj.weapon = $.extend({}, obj.weapon);
			obj.weapon.state = e.data.weapon;
			obj.controller = $.extend({}, obj.controller);
			obj.controller.state = e.data.controller;
		    } else if (is_pellet(obj)) {
			obj.time_to_live = e.data.time_to_live;
		    } else {
			// Planet has no other updatable state
		    }
		    objects[e.id] = obj;
		}
	    } else {
		// Should be {Planet, Ship, Pellet}.Create
                objects[e.id] = e.data;
		if (is_ship(e.data) && !(e.id in state.ship_colors)) {
		    state.ship_colors[e.id] = gen_ship_color();
		}
	    }
	});
	state.states.push(objects);
    });

    $('.player-seek').attr('max', state.states.length - 1);
    set_playing(true);
}

// -------------------- UI/loading --------------------

function read_jsonl(file, on_load) {
    var reader = new FileReader();
    reader.onload = function (e) {
	var log = [];
	var lines = e.target.result.split('\n');
	lines.forEach(function(line) {
	    if (line !== '') {
		log.push(JSON.parse(line));
	    }
	});
	on_load(log);
    };
    reader.readAsText(file);
}

function read_avro(file, on_load) {
    // TODO: this is broken
    avsc.createBlobDecoder(file, {'wrapUnions': true});
}

function set_filename(name) {
    $('.player-title').text(name || 'No replay loaded...');
}

function read_file(e) {
    // User is loading a new file - we should hide any old errors
    $('.alert').hide();
    set_filename();

    var file = e.target.files[0];
    if (file.name.endsWith(".jsonl") ||
	file.name.endsWith(".json")) {
	read_jsonl(file, setup_log);
	set_filename(file.name);

    } else {
	$('.alert-text').html(
	    '<strong>Failed to load ' + file.name + '</strong>' +
	    ' - extension not recognized (expected {.jsonl .json})');
	$('.alert').show();
    }
    // Reset the state - otherwise it doesn't do what you'd expect if you
    // reload the same file
    e.target.value = '';
}

function resize_canvas() {
    var width = $('.player-canvas-holder').width();
    $('.player-canvas')
	.attr('width', width)
	.attr('height', settings.canvas_aspect * width);
}

$(function() {
    set_playing(false);
    $('.player-start').on('click', function (e) {
	set_playing(false);
	seek(0);
    });
    $('.player-play').on('click', function (e) {
	set_playing(true);
    });
    $('.player-pause').on('click', function (e) {
	set_playing(false);
    });
    $('.player-restart').on('click', function (e) {
	seek(0);
	set_playing(true);
    });
    $('.player-end').on('click', function (e) {
	set_playing(false);
	seek(-1);
    });
    $('.player-seek').on('input', function (e) {
	seek(parseInt($(e.target).val()));
    });

    $('.alert').hide();
    $('.alert .close').on('click', function (e) {
	$(e.target).parent().hide();
    });

    set_filename();
    $('.replay-file').on('change', read_file);

    resize_canvas();
    $(window).resize(resize_canvas);

    window.setInterval(tick, settings.tick_time);
});

// $(function() {
//     var id = 'sample';  // TODO
//     $.get({url: '/replay/' + id,
//            cache: false
//           }).then(log_loaded);
// });

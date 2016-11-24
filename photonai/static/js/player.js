function draw(space_dimensions, objects) {
    var canvas = $(".player-canvas")[0];
    var ctx = canvas.getContext("2d");

    // The content should be centered and top aligned
    var scale = Math.min(canvas.width / space_dimensions.x,
                         canvas.height / space_dimensions.y);
    ctx.translate(0.5 * (canvas.width - scale * space_dimensions.x),
                  0.0);
    ctx.scale(scale, scale);

    // Clip to the dimensions of space, and fill it in
    ctx.beginPath();
    ctx.rect(0, 0, space_dimensions.x, space_dimensions.y);
    ctx.clip();
    ctx.fillStyle = '#000';
    ctx.fill();

    // Draw all the objects
    Object.values(objects).forEach(function(obj) {
        // Either has a body, or is a body!
        var body = ('body' in obj) ? obj['body'] : obj;
        var position = body.state.position;
        ctx.fillStyle = '#0ff';
        ctx.beginPath();
        ctx.arc(position.x, position.y, body.radius, 0, 2 * Math.PI);
        ctx.fill();
    });
}

function log_loaded(log) {
    // State
    var space_dimensions = log[0].data.dimensions;
    var objects = {};

    // Update the game objects
    var step = log[1].data;
    step.forEach(function (e) {
        if ('radius' in e.data || 'body' in e.data) {
            // Must be {body, ship, pellet}.Create
            if (e.id in objects) {
                console.error("Duplicate object ID (previous) " +
                              JSON.stringify(objects[e.id]) +
                              " and (new) " + JSON.stringify(e.data));
            } else {
                objects[e.id] = e.data;
            }
        }
    });
    // Draw the current state
    draw(space_dimensions, objects);
}

$(function() {
    var id = "sample";  // TODO

    $.get({url: "/replay/" + id,
           cache: false
          }).then(log_loaded);
});

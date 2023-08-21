const map_area = document.querySelector("#map-area");
const maw = map_area.clientWidth;
const mah = map_area.clientHeight;

console.log({maw, mah});
const canvas_dom = document.querySelector("#map-canvas");
canvas_dom.setAttribute("width", maw);
canvas_dom.setAttribute("height", mah);
const canvas = new fabric.Canvas('map-canvas', {width: maw, height: mah});
canvas.viewportTransform[4] = canvas.width / 2;
canvas.viewportTransform[5] = canvas.height / 2;
canvas.viewportTransform[0] = 0.5;
canvas.viewportTransform[3] = 0.5;



var circle = new fabric.Circle({
    top: 0,
    left: 0,
    radius: 5,
});
canvas.add(circle);

const robot = new fabric.Triangle({
    top: 0,
    left: 0,
    width: 60,
    height: 70,
    angle: 0,
    fill: 'black',
    originX: "center",
    originY: "center"
});
canvas.add(robot);

// set up zooming 
canvas.on('mouse:wheel', function(opt) {
  var delta = opt.e.deltaY;
  var zoom = canvas.getZoom();
  zoom *= 0.999 ** delta;
  if (zoom > 20) zoom = 20;
  if (zoom < 0.01) zoom = 0.01;
  canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
  opt.e.preventDefault();
  opt.e.stopPropagation();
});

// handle panning
var panning = false;
canvas.on('mouse:up', function (e) {
    panning = false;
});

canvas.on('mouse:down', function (e) {
    panning = true;
});
canvas.on('mouse:move', function (e) {
    if (panning && e && e.e) {
        var units = 10;
        var delta = new fabric.Point(e.e.movementX, e.e.movementY);
        canvas.relativePan(delta);
    }
});

var socket = io();
socket.on('connect', function() {
    console.log("connected");
});

socket.on('data', function(data) {
    robot.set({
        left: data['position'][0],
        top: -data['position'][1]
        // angle: -data['heading'] + 90
    });
    robot.rotate(-data['heading'] + 90);
    canvas.renderAll();
});

socket.on('data2', function(data) {
    console.log(data);
});

async function get_robot_data(robot_id) {
    const response = await fetch(`info/${robot_id}`);

    // Storing data in form of JSON
    var data = await response.json();
    robot_info_p.innerText = data['data'];
}

const socketc = io.connect();


// send data on click
canvas.on("mouse:dblclick", (event) => {
    var pointer = canvas.getPointer(event);
    console.log("pointer at", pointer);
    socketc.emit('datatest', pointer);
});

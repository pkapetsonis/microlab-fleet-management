// make all canvas objects not selectable by default
fabric.Object.prototype.selectable = false;

// compute canvas size
const map_area = document.querySelector("#map-area");
const maw = map_area.clientWidth;
const mah = map_area.clientHeight;

console.log({maw, mah});
// initialize fabric.js canvas
const canvas_dom = document.querySelector("#map-canvas");
canvas_dom.setAttribute("width", maw);
canvas_dom.setAttribute("height", mah);
const canvas = new fabric.Canvas('map-canvas', {width: maw, height: mah});
// finetune view matrix
canvas.viewportTransform[4] = canvas.width / 2;
canvas.viewportTransform[5] = canvas.height / 2;
canvas.viewportTransform[0] = 0.5;
canvas.viewportTransform[3] = 0.5;



var circle = new fabric.Circle({
    top: 0,
    left: 0,
    radius: 5,
    selectable: false,
    evented: false
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
    originY: "center",
    stroke: "red",
    strokeWidth: 5,
    selectable: false,
    evented: false
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
let timeout;
let statusb = false;
let lastPosX;
let lastPosY;
let PosX;
let PosY;
socket.on('connect', function() {
    console.log("connected");
    timeout = setTimeout(timedOutFunc, 1500);
});

socket.on('data', function(data) {
    PosX = data['position'][0]; 
    PosY = -data['position'][1];
    robot.set({
        left: PosX,
        top: PosY
        // angle: -data['heading'] + 90
    });
    if(typeof lastPosX === 'number') {
        var line = new fabric.Line([lastPosX, lastPosY,PosX, PosY], {
            stroke: 'black',
            strokeWidth: 4,
            selectable: false,
            evented: false
        });
        lines.addWithUpdate(line);
    }

    lastPosX = PosX;
    lastPosY = PosY;

    robot.rotate(-data['heading'] + 90);
    canvas.renderAll();
    refreshTimeout();
    if(statusb == false) {
        document.getElementById("status-image").src="../static/images/online.png";
        statusb = true;
    }
});

socket.on('data2', function(data) {
    console.log(data);
});

const socketc = io.connect();


// send data on click
canvas.on("mouse:dblclick", (event) => {
    var pointer = canvas.getPointer(event);
    console.log("pointer at", pointer);
    socketc.emit('datatest', pointer);
});

function timedOutFunc() {
    if(statusb == true) {
        document.getElementById("status-image").src="../static/images/offline.png";
        statusb = false;
        var line = new fabric.Line([lastPosX, lastPosY,PosX, PosY], {
            stroke: 'black',
            strokeWidth: 4,
            selectable: false,
            evented: false
        });
        lastPosX = undefined;
        lastPosY = undefined;
        lines.addWithUpdate(line);
    }
    refreshTimeout();
}

function refreshTimeout() {
    clearTimeout(timeout);
    timeout = setTimeout(timedOutFunc, 1500);
}

var lines = new fabric.Group({
    selectable: false,
    evented: false
});
canvas.add(lines);

document.getElementById('clear-path-b').onclick = function() {
    lines._objects.length = 0;
    lines.addWithUpdate();
    canvas.renderAll();
};

async function getmap() {
    const response = await fetch("/getmap");
    var polygons = await response.json();

    fjs_polys = polygons.map((ar) => {
        // console.log(ar);
        const points = ar.map(xy => ({x: xy[0], y: -xy[1]}));
        console.log(points);

        var polygon = new fabric.Polygon(points, {
            fill: 'green'
        });
      
        canvas.add(polygon);
        
    });

    canvas.renderAll();
}

getmap();
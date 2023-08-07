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

// fabric.Image.fromURL('/static/images/ev3-top-down.jpeg', function (oi) {
//     oi.set({width: 100, height:100});
//     canvas.add(oi);
// });

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

canvas.on("mouse:down", (event) => {
    var pointer = canvas.getPointer(event);
    console.log("Coordinates of the pointer relative to the object are: ", pointer);
    socketc.emit('datatest', pointer);
});
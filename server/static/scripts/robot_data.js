
const robot_info_p = document.querySelector("#robot-info");
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
   radius: 30,
});

canvas.add(circle);
const dummy = new fabric.Triangle({
 top: 100,
 left: 100,
 width: 60,
 height: 70,
 angle: 0,
 fill: 'black',
});

fabric.Image.fromURL('/static/images/ev3-top-down.jpeg', function (oi) {
    oi.set({width: 100, height:100});
    canvas.add(oi);
});
canvas.add(dummy);

var socket = io();
socket.on('connect', function() {
    console.log("connected");
});

socket.on('data', function(data) {
    //console.log(data);
    // dummy.set({angle : data['state']});
    // const state = data['state'];
    //dummy.angle(data['heading']);
    const freq = 0.01;
    dummy.set({
        left: data['position'][0],
        top: -data['position'][1],
        angle: -data['heading'] + 90
    });
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

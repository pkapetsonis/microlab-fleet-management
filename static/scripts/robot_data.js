
const robot_info_p = document.querySelector("#robot-info");
const map_area = document.querySelector("#map-area");
const maw = map_area.clientWidth;
const mah = map_area.clientHeight;

console.log({maw, mah});
const canvas_dom = document.querySelector("#map-canvas");
canvas_dom.setAttribute("width", maw);
canvas_dom.setAttribute("height", mah);
const canvas = new fabric.Canvas('map-canvas', {width: maw, height: mah});
const dummy = new fabric.Rect({
 top: 100,
 left: 100,
 width: 60,
 height: 70,
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
    const state = data['state'];
    dummy.rotate(2*state);
    const freq = 0.01;
    dummy.set({
        left: 400 + 100* Math.cos(freq*state),
        top: 400 + 100* Math.sin(freq*state)
    });
    canvas.renderAll();
})

async function get_robot_data(robot_id) {
    const response = await fetch(`info/${robot_id}`);

    // Storing data in form of JSON
    var data = await response.json();
    robot_info_p.innerText = data['data'];
}

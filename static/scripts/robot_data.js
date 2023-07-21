
const robot_info_p = document.querySelector("#robot-info");
const map_area = document.querySelector("#map-area");
const maw = map_area.clientWidth;
const mah = map_area.clientHeight;

console.log({maw, mah});
const canvas_dom = document.querySelector("#map-canvas");
canvas_dom.setAttribute("width", maw);
canvas_dom.setAttribute("height", mah);
const canvas = new fabric.Canvas('map-canvas', {width: maw, height: mah});
const rect = new fabric.Rect({
 top: 100,
 left: 100,
 width: 60,
 height: 70,
 fill: 'black',
});
canvas.add(rect);

var socket = io();
socket.on('connect', function() {
    console.log("connected");
});

socket.on('data', function(data) {
    console.log(data);
})

async function get_robot_data(robot_id) {
    const response = await fetch(`info/${robot_id}`);

    // Storing data in form of JSON
    var data = await response.json();
    robot_info_p.innerText = data['data'];
}


const robot_info_p = document.querySelector("#robot-info");


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
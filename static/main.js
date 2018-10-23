function nextMatches(sid) {
    var r = new XMLHttpRequest();
    var path;
    if (sid == -1) {
        path = '/m/group/next';
    } else {
        path = '/m/' + sid + '/next';
    }
    r.open('POST', path, true);
    r.send();
}

var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', () => {
//    alert('Connected!');
});

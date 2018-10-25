function nextMatches(sid) {
    console.log('Next matches for ' + sid);
    var path;
    if (sid == -1) {
        path = 'm/group/next';
    } else {
        path = 'm/' + sid + '/next';
    }
    var req = new XMLHttpRequest();
    req.addEventListener("load", () => {
        console.log('Success');
        //setTimeout(() => { window.location.reload(false); }, 500);
    });
    req.open("POST", window.location + path);
    req.send();
}

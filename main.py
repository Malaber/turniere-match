from flask import Flask, render_template, request, redirect, Response
from flask_socketio import SocketIO

from turniere import Turniere

import logging


logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme(:'
socketio = SocketIO(app)


#base_url = 'https://turnie.re'
#base_url = 'http://10.21.255.159:8080'
base_url = 'http://10.8.0.46:8080'
#tournament_code = '55pzr'
#tournament_code = '58ib7'
tournament_code = 'hvdx1'

username = 'test@test'
password = '1' * 12

t = Turniere(base_url, tournament_code)
t.login(username, password)


@app.route('/')
def index():
    matches = list(map(lambda m: m['data'], t.get_matches()))
    stages = {}
    for match in matches:
        stageid = match['stageid']
        stages.setdefault(stageid, [])
        stages[stageid].append(match)
    stages_sorted = list(sorted(stages.items(), key=lambda s: s[0], reverse=True))
    return render_template('index.jinja2', stages=stages_sorted)


@app.route('/m/next', methods=['POST'])
def next_matches():
    t.next_group_matches()
    return Response(status=204)


@app.route('/m/<sid>/next', methods=['POST'])
def next_stage_matches(sid):
    t.next_stage_matches(sid)
    return Response(status=204)


@app.route('/m/<mid>/submit', methods=['POST'])
def submit_match_result(mid):
    request_form = request.form
    t.submit_results(mid, request_form['score1'], request_form['score2'], 'isLive' in request_form)
    return redirect('/')


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8080, debug=True)

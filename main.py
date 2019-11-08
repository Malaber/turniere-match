import logging

from flask import Flask, redirect, render_template, request

from turniere import Turniere
from worker import Action, Match, Worker

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme(:'

username = 'test@test.test'
password = 'testtest'

tournament_code = '16'
main_instance = Turniere(
    'http://localhost:3001', tournament_code, username, password
)

remote_instance = Turniere(
    'https://api01.turnie.re', tournament_code, username, password
)

w = Worker(remote_instance)


@app.route('/')
def index():
    stages = main_instance.get_stages()
    stages_simplified = []
    for stage in stages:
        groups = stage['groups']
        if groups:
            for group in groups:
                stages_simplified.append({
                    'id': stage['id'],
                    'group': True,
                    'level': group['number'],
                    'matches': sorted(group['matches'], key=lambda m: m['position']),
                })
        else:
            stages_simplified.append({
                'id': stage['id'],
                'group': False,
                'level': stage['level'],
                'matches': sorted(filter(
                    lambda m: m['state'] != 'not_ready', stage['matches']
                ), key=lambda m: m['position']),
            })
    return render_template('index.jinja2', stages=stages_simplified)


@app.route('/m/<sid>/next', methods=['POST'])
def next_stage_matches(sid):
    main_instance.login()
    if sid == 'group':
        main_instance.next_group_matches()
        w.queue.put_nowait(Action('next_group_matches', None))
    else:
        main_instance.next_stage_matches(str(sid))
        w.queue.put_nowait(Action('next_stage_matches', sid))
    return redirect('/')


@app.route('/m/<mid>/submit', methods=['POST'])
def submit_match_result(mid):
    request_form = request.form
    matchscore1 = request_form['matchscore1']
    matchscore2 = request_form['matchscore2']
    score1 = request_form['score1']
    score2 = request_form['score2']
    is_livescore = 'isLive' in request_form
    match = Match(mid, matchscore1, matchscore2, score1, score2, is_livescore)
    main_instance.login()
    main_instance.submit_results(match)
    w.queue.put_nowait(Action('submit_results', match))
    return redirect('/#match-' + match.mid)


@app.route('/m/<sid>/stop', methods=['POST'])
def stop_group_stage(sid):
    main_instance.login()
    main_instance.stop_group_stage(sid)
    w.queue.put_nowait(Action('stop_group_stage', sid))
    return redirect('/')


if __name__ == '__main__':
    w.start()
    app.run(host='0.0.0.0', port=7070, debug=True)

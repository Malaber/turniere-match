from flask import Flask, redirect, render_template, request

from turniere import Turniere
from worker import Match, Worker

import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme(:'

username = 'schaedlerdaniel@icloud.com'
password = '3t9%oCL6$b&RzK86FjnlmEMHayB!h*Q69ML'

tournament_code = '39l3r'
main_instance = Turniere(
    'http://10.8.0.46:8080', tournament_code, username, password
)

remote_instance = Turniere(
    'https://turnie.re', tournament_code, username, password
)

w = Worker(remote_instance)


@app.route('/')
def index():
    matches = list(map(lambda m: m['data'], main_instance.get_matches()))
    stages = {}
    for match in matches:
        stageid = match['stageid']
        stages.setdefault(stageid, [])
        stages[stageid].append(match)
    stages_sorted = list(
        sorted(stages.items(), key=lambda s: s[0], reverse=True)
    )
    return render_template('index.jinja2', stages=stages_sorted)


@app.route('/m/<sid>/next', methods=['POST'])
def next_stage_matches(sid):
    main_instance.login()
    if sid == 'group':
        main_instance.next_group_matches()
        w.queue.put_nowait('group')
    else:
        main_instance.next_stage_matches(str(sid))
        w.queue.put_nowait(int(sid))
    return redirect('/')


@app.route('/m/<mid>/submit', methods=['POST'])
def submit_match_result(mid):
    request_form = request.form
    score1 = request_form['score1']
    score2 = request_form['score2']
    is_livescore = 'isLive' in request_form
    match = Match(mid, score1, score2, is_livescore)
    main_instance.login()
    main_instance.submit_results(mid, score1, score2, is_livescore)
    w.queue.put_nowait(match)
    return redirect('/#match-' + match.mid)


if __name__ == '__main__':
    w.start()
    app.run(host='0.0.0.0', port=7070, debug=True)

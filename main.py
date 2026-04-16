import logging
import os
import uuid

from flask import Flask, jsonify, redirect, render_template, request
from flask_socketio import SocketIO, join_room
from datetime import datetime, timedelta

from config import read_config, MatchConfiguredToNotRunError
from turniere import Turniere, TurniereRequestError
from worker import Action, Match, Worker

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme(:'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def get_uuid():
    return str(uuid.uuid4())

try:
    config = read_config()
except MatchConfiguredToNotRunError:
    print("Match is configured to not run. Exiting.")
    exit(0)

app.jinja_env.globals.update(get_uuid=get_uuid)

main_instance = Turniere(
    config.main_instance_url, config.tournament_code, config.username, config.password
)

remote_instance = Turniere(
    config.remote_instance_url, config.tournament_code, config.username, config.password
    ) if config.remote_instance_url and config.remote_instance_url != config.main_instance_url else None

w = Worker(remote_instance) if remote_instance else None


def enqueue_remote_action(action):
    if w is not None:
        w.queue.put_nowait(action)


def local_timezone():
    return datetime.now().astimezone().tzinfo


def normalize_timer_end(timer_end):
    parsed_time = datetime.fromisoformat(timer_end)
    if parsed_time.tzinfo is None:
        parsed_time = parsed_time.replace(tzinfo=local_timezone())
    return parsed_time.isoformat(timespec='seconds')


def get_stage_name(sid):
    if sid == 0:
        return 'Finale'
    elif sid == 1:
        return 'Halbfinale'
    elif sid == 2:
        return 'Viertelfinale'
    elif sid == 3:
        return 'Achtelfinale'
    else:
        return f'{2 ** sid}tel-Finale'


def query_error():
    error = request.args.get('error')
    if not error:
        return None

    if error == 'decider_required':
        return 'Playoffs können noch nicht gestartet werden. Für einen relevanten Gleichstand muss zuerst ein Entscheidungsmatch gespielt werden.'

    if error == 'group_stage_not_over':
        return 'Die Gruppenphase kann noch nicht beendet werden. Es laufen noch Spiele oder es fehlen Ergebnisse.'

    return 'Die Aktion konnte nicht ausgeführt werden.'

@app.route('/')
def index():
    timer = main_instance.get_timer_end()
    stages = main_instance.get_stages()
    stages_simplified = []
    for stage in stages:
        groups = stage['groups']
        if groups:
            for group in groups:
                stages_simplified.append({
                    'id': stage['id'],
                    'group': True,
                    'group_id': group['id'],
                    'level': group['number'],
                    'matches': sorted(group['matches'], key=lambda m: m['position']),
                    'name': "Gruppe " + str(group['number']),
                })
        else:
            stages_simplified.append({
                'id': stage['id'],
                'group': False,
                'level': stage['level'],
                'matches': sorted(filter(
                    lambda m: m['state'] != 'not_ready', stage['matches']
                ), key=lambda m: m['position']),
                'name': get_stage_name(stage['level']),
            })
    return render_template('index.jinja2', stages=stages_simplified, timer=timer, error_message=query_error())


@app.route('/groups/<gid>/table')
def group_table(gid):
    group = main_instance.get_group(gid)
    group_scores = sorted(group['group_scores'], key=lambda score: score['position'])
    return jsonify({
        'id': group['id'],
        'number': group['number'],
        'decider_matches': [match for match in group['matches'] if match.get('decider')],
        'scores': group_scores,
    })

@app.route('/teams')
def teams():
    teams = main_instance.get_teams()
    return render_template('teams.jinja2', teams=teams)


@app.route('/m/<sid>/next', methods=['POST'])
def next_stage_matches(sid):
    main_instance.login()
    if sid == 'group':
        main_instance.next_group_matches()
        enqueue_remote_action(Action('next_group_matches', None))
    else:
        main_instance.next_stage_matches(str(sid))
        enqueue_remote_action(Action('next_stage_matches', sid))
    return redirect('/')


@app.route('/m/<mid>/submit', methods=['POST'])
def submit_match_result(mid):
    request_form = request.form
    matchscore1 = request_form['match_score1']
    matchscore2 = request_form['match_score2']
    score1 = request_form['score1']
    score2 = request_form['score2']
    is_livescore = 'isLive' in request_form
    score_field = request_form.get('score_field', 'points')
    match = Match(mid, matchscore1, matchscore2, score1, score2, is_livescore, score_field)
    main_instance.login()
    main_instance.submit_results(match)
    enqueue_remote_action(Action('submit_results', match))
    return redirect('/#match-' + match.mid)


@app.route('/groups/<gid>/matches', methods=['POST'])
def create_decider_match(gid):
    team_ids = [request.form.get('team_id_1'), request.form.get('team_id_2')]
    team_ids = [int(team_id) for team_id in team_ids if team_id]
    main_instance.login()
    match = main_instance.create_decider_match(gid, team_ids)
    enqueue_remote_action(Action('create_decider_match', (gid, team_ids)))
    return redirect('/#match-' + str(match['id']))


@app.route('/m/<sid>/stop', methods=['POST'])
def stop_group_stage(sid):
    main_instance.login()
    try:
        main_instance.stop_group_stage(sid)
    except TurniereRequestError as error:
        if error.status_code == 422:
            body = error.body if isinstance(error.body, dict) else {}
            if body.get('blocking_ties'):
                return redirect('/?error=decider_required')
            if body.get('error') == 'Group Stage still has some matches that are not over yet. Finish them to generate playoffs':
                return redirect('/?error=group_stage_not_over')
        raise
    enqueue_remote_action(Action('stop_group_stage', sid))
    return redirect('/')

@app.route('/t/<tid>', methods=['POST'])
def update_team_name(tid):
    new_name = request.form['name']
    main_instance.login()
    main_instance.update_team_name(tid, new_name)
    enqueue_remote_action(Action('update_team_name', (tid, new_name)))
    return redirect('/teams')

@app.route('/set_timer', methods=['POST'])
def set_timer():
    end_time = normalize_timer_end(request.form['end_time'])
    main_instance.login()
    try:
        main_instance.set_timer_end(end_time)
        enqueue_remote_action(Action('set_timer_end', end_time))
    except ValueError as e:
        logging.error(f"Failed to set timer: {e}")
        return redirect('/?error=invalid_time')
    return redirect('/')

@app.route('/set_timer_seconds', methods=['POST'])
def set_timer_seconds():
    timer_end_seconds = request.form['timer_end_seconds']
    main_instance.login()
    try:
        # we do the calculation of seconds to timestamp ourselves as this is timesensitive and both backends should match
        timer_end_seconds = int(timer_end_seconds)
        future_time = datetime.now().astimezone() + timedelta(seconds=timer_end_seconds)
        future_time_str = future_time.isoformat(timespec='seconds')
        main_instance.set_timer_end(future_time_str)
        enqueue_remote_action(Action('set_timer_end', future_time_str))
    except ValueError as e:
        logging.error(f"Failed to set timer in seconds: {e}")
        return redirect('/?error=invalid_seconds')
    return redirect('/')

DISPLAY_STATES = [
    ('matches_all', 'Alle Matches'),
    ('matches_in_progress', 'Laufende Matches'),
    ('matches_upcoming', 'Kommende Matches'),
    ('matches_not_started', 'Bereit zum Starten'),
    ('matches_finished', 'Beendete Matches'),
    ('groups', 'Gruppenstand'),
    ('between_games', 'Zwischen den Spielen'),
    ('during_game', 'Während dem Spiel'),
]


@app.route('/beamers')
def beamers_page():
    main_instance.login()
    beamers = main_instance.get_beamers()
    return render_template('beamers.jinja2', beamers=beamers,
                           display_states=DISPLAY_STATES)


@app.route('/beamer/create', methods=['POST'])
def create_beamer():
    name = request.form['name']
    display_state = request.form.get('display_state', 'matches_all')
    qr_code_url = request.form.get('qr_code_url') or None
    logo_url = request.form.get('logo_url') or None
    main_instance.login()
    main_instance.create_beamer(name, display_state, qr_code_url, logo_url)
    enqueue_remote_action(Action('create_beamer', (name, display_state, qr_code_url, logo_url)))
    return redirect('/beamers')


@app.route('/beamer/<bid>/update', methods=['POST'])
def update_beamer_state(bid):
    new_state = request.form['display_state']
    main_instance.login()
    beamer = main_instance.get_beamer(bid)
    main_instance.update_beamer(bid, display_state=new_state)
    enqueue_remote_action(Action('update_beamer', (beamer['name'], new_state)))
    socketio.emit('beamer_state_changed', {
        'beamer_name': beamer['name'],
        'display_state': new_state,
    }, to='beamer_' + beamer['name'])
    return redirect('/beamers')


@app.route('/beamer/<bid>/delete', methods=['POST'])
def delete_beamer(bid):
    main_instance.login()
    beamer = main_instance.get_beamer(bid)
    main_instance.delete_beamer(bid)
    enqueue_remote_action(Action('delete_beamer', beamer['name']))
    return redirect('/beamers')


@socketio.on('connect')
def handle_connect():
    logging.info('Fullscreen client connected via Socket.IO')


@socketio.on('join_beamer')
def handle_join_beamer(data):
    beamer_name = data.get('beamer_name', 'default')
    join_room('beamer_' + beamer_name)
    logging.info(f'Client joined room beamer_{beamer_name}')


if __name__ == '__main__':
    if w is not None:
        w.start()
    socketio.run(
        app,
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', '7070')),
        debug=os.environ.get('DEBUG', 'true').lower() == 'true',
    )

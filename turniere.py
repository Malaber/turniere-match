import logging
import datetime
import requests


class TurniereRequestError(Exception):
    def __init__(self, method, path, response):
        self.method = method
        self.path = path
        self.status_code = response.status_code if response is not None else None
        self.response = response
        try:
            self.body = response.json()
        except Exception:
            self.body = response.text if response is not None else ''

        super().__init__(f'{method} {path} failed with status {self.status_code}: {self.body}')


class Turniere(object):
    def __init__(self, base_url, tournament_code, email, password):
        self.base_url = base_url
        self.tournament_code = tournament_code
        self.email = email
        self.password = password
        self.request_headers = {}

    def _request(self, path, method='GET', json=None):
        s = requests.Session()
        req = requests.Request(
            method,
            self.base_url + path,
            headers=self.request_headers,
            json=json or {}
        )
        r = s.send(req.prepare())
        if r:
            return r
        else:
            raise TurniereRequestError(method, path, r)

    def _start_match(self, mid):
        self._request(f'/matches/{mid}', method='PATCH', json={
            'state': 'in_progress'
        })

    def login(self):
        r = self._request(
            '/users/sign_in',
            method='POST',
            json={
                'email': self.email,
                'password': self.password
            }
        )
        if not r:
            raise Exception(f'Login failed: {r}')
        headers = r.headers
        self.request_headers = {
            'Access-Token': headers['Access-Token'],
            'Client': headers['Client'],
            'Uid': headers['Uid'],
        }

    def get_stages(self):
        return self._request(
            f'/tournaments/{self.tournament_code}'
        ).json()['stages']

    def get_group(self, gid):
        return self._request(f'/groups/{gid}').json()

    def next_stage_matches(self, sid):
        logging.info('Starting next playoff matches for %d', sid)
        # fetch stage
        stage = self._request(f'/stages/{sid}').json()
        for match in stage['matches']:
            self._start_match(match['id'])

    def next_group_matches(self):
        # fetch groups
        logging.info('Starting new group matches')
        groups = list(filter(lambda s: s['level'] == -1, self._request(
            f'/tournaments/{self.tournament_code}'
        ).json()['stages']))[0]['groups']
        # start first not started match in each group
        for group in groups:
            target_matches = list(sorted(
                filter(lambda m: m['state'] == 'not_started', group['matches']),
                key=lambda m: m['position'],
            ))
            if target_matches:
                self._start_match(target_matches[0]['id'])
            else:
                logging.info(
                    'Tried to start next matches, but there aren\'t any'
                )

    def stop_group_stage(self, sid):
        self._request(f'/stages/{sid}', method='PATCH', json={
            'state': 'finished'
        })

    def submit_results(self, match):
        score_field = match.score_field or 'points'
        self._request(
            f'/match_scores/{match.matchscore1}', method='PATCH', json={
                score_field: match.score1
            }
        )
        self._request(
            f'/match_scores/{match.matchscore2}', method='PATCH', json={
                score_field: match.score2
            }
        )
        if not match.is_live:
            # end match
            self._request(f'/matches/{match.mid}', method='PATCH', json={
                'state': 'finished'
            })

    def create_decider_match(self, gid, team_ids):
        return self._request(f'/groups/{gid}/matches', method='POST', json={
            'team_ids': team_ids
        }).json()

    def get_teams(self):
        return self._request(
            f'/tournaments/{self.tournament_code}'
        ).json()['teams']

    def update_team_name(self, tid, name):
        self._request(f'/teams/{tid}', method='PATCH', json={
            'name': name
        })

    def get_timer_end(self):
        json = self._request(f'/tournaments/{self.tournament_code}/timer_end').json()
        return json['timer_end']

    def set_timer_end(self, timer_end):
        # Validate timer_end
        if not timer_end:
            raise ValueError('Timer end is required')

        try:
            parsed_time = datetime.datetime.fromisoformat(timer_end)
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
            if parsed_time <= datetime.datetime.now(tz=parsed_time.tzinfo):
                raise ValueError('Timer end must be in the future')
        except ValueError as e:
            raise ValueError(f'Invalid datetime format: {e}')

        # Send PATCH request
        self._request(f'/tournaments/{self.tournament_code}/set_timer_end', method='PATCH', json={
            'timer_end': timer_end
        })

    def set_timer_end_seconds(self, timer_end_seconds):
        # Validate timer_end_seconds
        if not isinstance(timer_end_seconds, int) or timer_end_seconds <= 0:
            raise ValueError('Timer end seconds must be a positive integer')

        # Send PATCH request with timer_end_seconds
        self._request(f'/tournaments/{self.tournament_code}/set_timer_end', method='PATCH', json={
            'timer_end_seconds': timer_end_seconds
        })

    # --- Beamer management ---

    def get_beamers(self):
        return self._request(f'/tournaments/{self.tournament_code}/beamers').json()

    def get_beamer(self, bid):
        return self._request(f'/tournaments/{self.tournament_code}/beamers/{bid}').json()

    def get_beamer_by_name(self, name):
        return self._request(
            f'/tournaments/{self.tournament_code}/beamers/by_name?name={name}'
        ).json()

    def create_beamer(self, name, display_state='matches_all',
                      qr_code_url=None, logo_url=None):
        payload = {
            'name': name,
            'display_state': display_state,
        }
        if qr_code_url:
            payload['qr_code_url'] = qr_code_url
        if logo_url:
            payload['logo_url'] = logo_url
        return self._request(
            f'/tournaments/{self.tournament_code}/beamers',
            method='POST', json=payload
        ).json()

    def update_beamer(self, bid, **kwargs):
        return self._request(
            f'/tournaments/{self.tournament_code}/beamers/{bid}',
            method='PATCH', json=kwargs
        ).json()

    def update_beamer_by_name(self, name, display_state):
        beamer = self.get_beamer_by_name(name)
        return self.update_beamer(beamer['id'], display_state=display_state)

    def delete_beamer(self, bid):
        self._request(
            f'/tournaments/{self.tournament_code}/beamers/{bid}',
            method='DELETE'
        )

    def delete_beamer_by_name(self, name):
        beamer = self.get_beamer_by_name(name)
        self.delete_beamer(beamer['id'])

import logging
import datetime
import requests


class Turniere(object):
    def __init__(self, base_url, tournament_code, email, password):
        self.base_url = base_url
        self.tournament_code = tournament_code
        self.email = email
        self.password = password
        self.request_headers = {}

    def _request(self, path, method='GET', json={}):
        s = requests.Session()
        req = requests.Request(
            method,
            self.base_url + path,
            headers=self.request_headers,
            json=json
        )
        r = s.send(req.prepare())
        if r:
            return r
        else:
            raise Exception(f'Invalid response: {r}: {r.json()}')

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
        self._request(
            f'/match_scores/{match.matchscore1}', method='PATCH', json={
                'points': match.score1
            }
        )
        self._request(
            f'/match_scores/{match.matchscore2}', method='PATCH', json={
                'points': match.score2
            }
        )
        if not match.is_live:
            # end match
            self._request(f'/matches/{match.mid}', method='PATCH', json={
                'state': 'finished'
            })

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
            parsed_time = datetime.datetime.strptime(timer_end, '%Y-%m-%dT%H:%M')
            if parsed_time is None:
                raise ValueError('Invalid datetime format')
            if parsed_time <= datetime.datetime.now():
                raise ValueError('Timer end must be in the future')
        except ValueError as e:
            raise ValueError(f'Invalid datetime format: {e}')

        # Send PATCH request
        self._request(f'/tournaments/{self.tournament_code}/set_timer_end', method='PATCH', json={
            'timer_end': timer_end
        })

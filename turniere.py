import logging

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
            raise Exception(f'Invalid response: {r}')

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
        # fetch stage
        stage = self._request(f'/stages/{sid}').json()
        match_patch = {
            'state': 'in_progress'
        }
        for match in stage['matches']:
            mid = match['id']
            # start match
            self._request(f'/matches/{mid}', method='PATCH', json=match_patch)

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

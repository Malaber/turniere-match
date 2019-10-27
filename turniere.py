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
        elif r.status_code in [401, 403]:
            logging.debug(r.text)
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
        return self._request(f'/tournaments/{self.tournament_code}')['stages']

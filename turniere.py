import requests

class Turniere(object):
    def __init__(self, base_url, tournament_code, username, password):
        self.base_url = base_url
        self.tournament_code = tournament_code
        self.username = username
        self.password = password
        self.request_headers = {}

    def _request(self, path, method='GET'):
        r = requests.get(self.base_url + path)
        if r:
            return r.json()
        else:
            raise Exception('Invalid response: {}'.format(r))

    def get_stages(self):
        return self._request('/tournaments/{}'.format(self.tournament_code))['stages']

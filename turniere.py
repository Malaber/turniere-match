import mechanicalsoup
from requests import Request


class Turniere(object):
    def __init__(self, base_url, tournament_code, username, password):
        self.base_url = base_url
        self.tournament_code = tournament_code
        self.username = username
        self.password = password
        self.browser = mechanicalsoup.StatefulBrowser()

    def _prepare_request(self, path, method='GET', json=None):
        request = Request(method, self.base_url + path, json=json)
        prepared_request = self.browser.session.prepare_request(request)
        return prepared_request

    def _send_request(self, path, method='GET'):
        request = self._prepare_request(path, method)
        return self.browser.session.send(request)

    def login(self, username=None, password=None):
        self.browser.open(self.base_url + '/login')
        self.browser.select_form('form[action="/login"]')
        self.browser['username'] = username or self.username
        self.browser['password'] = password or self.password
        self.browser.submit_selected()

    def get_matches(self):
        r = self._send_request('/m/t/' + self.tournament_code)
        if r:
            return r.json()
        else:
            raise Exception('Invalid response: {}'.format(r))

    def submit_results(self, mid, score1, score2, live=False):
        tournament_page = self.browser.open(
            self.base_url + '/t/' + self.tournament_code
        )
        csrf_token = tournament_page.soup.find(
            'meta', {'name': '_csrf'}
        )['content']
        csrf_header = tournament_page.soup.find(
            'meta', {'name': '_csrf_header'}
        )['content']
        data = {
            'live': live,
            'score1': score1,
            'score2': score2
        }
        request = self._prepare_request(
            '/m/' + str(mid), method='POST', json=data
        )
        request.headers[csrf_header] = csrf_token
        return self.browser.session.send(request)

    def next_group_matches(self):
        return self._send_request('/t/' + self.tournament_code + '/group/next')

    def next_stage_matches(self, sid):
        return self._send_request(
            '/t/' + self.tournament_code + '/' + sid + '/start'
        )

import sys

from turniere import Turniere


if __name__ == '__main__':
    name = sys.argv[1]
    #t = Turniere('https://api01.turnie.re', '', 'test@test.test', 'testtest')
    t = Turniere('http://localhost:3000', '', 'test@test.test', 'testtest')
    t.login()
    t._request('/tournaments', method='POST', json={
        'name': name,
        'description': '',
        'public': False,
        'group_stage': True,
        'playoff_teams_amount': 64,
        'teams': [
            {"name": f'{group}.{team}', "group": group}
            for team in range(5)
            for group in range(33)
        ]
    })

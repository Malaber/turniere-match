import sys

from turniere import Turniere


if __name__ == '__main__':
    name = sys.argv[1]
    t = Turniere('https://api01.turnie.re', '', 'test@test.test', 'testtest')
    t.login()
    t._request('/tournaments', method='POST', json={
        "name": name,
        "description": "",
        "public": False,
        "group_stage": True,
        "playoff_teams_amount": 2,
        "teams": [
            {"name": "01", "group": 0},
            {"name": "02", "group": 0},
            {"name": "03", "group": 0},
            {"name": "04", "group": 1},
            {"name": "05", "group": 1},
            {"name": "06", "group": 1},
            {"name": "07", "group": 2},
            {"name": "08", "group": 2},
            {"name": "09", "group": 2},
            {"name": "10", "group": 3},
            {"name": "11", "group": 3},
            {"name": "12", "group": 3}
        ]
    })

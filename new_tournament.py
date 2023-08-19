import random
import csv

from config import read_config
from turniere import Turniere


config = read_config()

if __name__ == '__main__':
    t = Turniere(config.main_instance_url, '', config.username, config.password)
    t.login()

    teams = []
    with open('t7_checkin.csv', newline='') as csvfile:
        turniere_checkin_csv = csv.DictReader(csvfile, delimiter=',')
        for row in turniere_checkin_csv:
            teams.append(row['Team Name'])

    random.shuffle(teams)
    teams = teams[:128]

    groups = zip(*([iter(teams)] * 4))
    teams_with_groups = []
    for num, group in enumerate(groups):
        for team in group:
            teams_with_groups.append({
                "name": team,
                "group": num
            })

    print(teams_with_groups)
    t._request('/tournaments', method='POST', json={
        "name": "7. Beerpong Turnier",
        "description": "7. Beerpong Turnier von Beerpong Weinstraße",
        "public": True,
        "group_stage": True,
        "teams": teams_with_groups,
        "playoff_teams_amount": 64
    })

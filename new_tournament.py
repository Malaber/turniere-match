import random
import csv

from config import read_config
from turniere import Turniere

"""
Reads exported pretix csv, takes the first 128 teams and posts them to turniere backen locally.
After tournament generation push db to remote instance
"""


config = read_config()

if __name__ == '__main__':
    t = Turniere(config.main_instance_url, '', config.username, config.password)
    t.login()

    teams = []
    with open('t9_checkin.csv', newline='') as csvfile:
        turniere_checkin_csv = csv.DictReader(csvfile, delimiter=',')
        for row in turniere_checkin_csv:
            teams.append(row['Team Name'])

    random.shuffle(teams)
    teams = teams[:128]

    # import collections
    # print([item for item, count in collections.Counter(teams).items() if count > 1])

    groups = zip(*([iter(teams)] * 4))
    teams_with_groups = []
    for num, group in enumerate(groups):
        for team in group:
            teams_with_groups.append({
                "name": team,
                "group": num
            })

    for team_with_group in teams_with_groups:
        print(team_with_group)

    print(t._request('/tournaments', method='POST', json={
        "name": "TEST 9",
        "description": "Diese matchups sind nicht korrekt, nur ein Test",
        "public": True,
        "group_stage": True,
        "teams": teams_with_groups,
        "playoff_teams_amount": 64
    }))

    infotext = "Push db to remote instance now!!"
    print()
    print(infotext)
    print(infotext)
    print(infotext)

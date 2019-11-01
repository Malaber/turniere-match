from turniere import Turniere

import logging
logging.basicConfig(level=logging.DEBUG)

t = Turniere('https://api01.turnie.re', '26', 'test@test.test', 'testtest')
t.login()
# for match in t.get_matches()[1:]:
#     t.submit_results(match['id'], 1, 2, False)

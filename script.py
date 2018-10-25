from turniere import Turniere
t = Turniere('http://10.8.0.46:8080', '39l3r', 'schaedlerdaniel@icloud.com', '3t9%oCL6$b&RzK86FjnlmEMHayB!h*Q69ML')
t.login()
for match in t.get_matches()[1:]:
    t.submit_results(match['id'], 1, 2, False

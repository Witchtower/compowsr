import re
import requests

class CareerProfile:
    def __init__(self, region, battletag):
        # get page source
        url = 'https://playoverwatch.com/de-de/career/pc/%s/%s' % (region, battletag.replace('#', '-'))

        self.html = requests.get(url).text

        # get competetive rank area

        xpr = '<div class="competitive-rank"><img src="https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-(\d).png"/><div class="u-align-center h6">(\d+)</div></div>'
        m = re.search(xpr, self.html)
        ranks = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster', 'top500']


        self.rank = ranks[int(m.group(1))-1] # ranks array 0-index, icons on website are 1-indexed

        self.sr = m.group(2)

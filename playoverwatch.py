import requests
import re
class CarreerProfile:
    def __init__(self, region, btag):
        # get page source
        url='https://playoverwatch.com/de-de/career/pc/%s/%s' % (region, battletag.replace('#', '-'))

        self.html = requests.get(url).text

        # get current sr and highest rank of season
        #<div class="competitive-rank">
        #    <img src="https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-4.png"/>
        #    <div class="u-align-center h6">2828</div>
        #</div>
        xpr = '<div class="competitive-rank"><img src="https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-(\d).png"/><div class="u-align-center h6">(\d+)</div></div>'
        m = re.search(xpr, resp.text)
        ranks = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster', 'top500']

        self.rank = ranks[m.group(1)]

        self.sr = m.group(2)
        


        # get season high

###
# Supybot-wizaz plugin
# Copyright (c) 2016, ACz
#
# A plugin to look for cosmetics' reviews from popular polish beauty
# site Wizaz.pl and present the results directly on your IRC channel.
#
###

import mechanize
import re
from unidecode import unidecode
from BeautifulSoup import BeautifulSoup

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Wizaz')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


# Colour characters supported by IRC clients
RED = '\x0304'
ORANGE = '\x0307'
YELLOW = '\x0308'
GREEN = '\x0309'
PINK = '\x0313'
BROWN = '\x0305'
PURPLE = '\x0306'
WHITE = '\x0300'
BOLD = '\x02'

TC = GREEN
RA = '\x0F'

MAIN_PAGE = 'http://wizaz.pl/kosmetyki/'
SEARCH_LINK = 'http://wizaz.pl/kosmetyki/szukaj.php'
NA = RED + 'N/A' + RA


class Wizaz(callbacks.Plugin):
    threaded = True

    def _tenstars(self, rate):
        ratebar = list('++++++++++')
        if rate <= 5:
            stars = int(round(rate*2))
            if stars >= 9:
                color = GREEN
            elif stars in [8,7,6]:
                color = YELLOW
            else:
                color = RED
            for i in range(stars):
                ratebar[i] = color + '@'
	    ratebar.insert(stars, PURPLE)
            ratebar.append(WHITE)
        return ratebar


    def wizaz(self, irc, msg, args, text):
        """<product name>

        This option looks for a product in Wizaz.pl KWC (popular database of 
        cosmetics reviews), scraps information from the site and presents the 
        most accurate result of the search. In this version it shows only one
        entry, so try to be precise in typing your keywords.
        """

        browser = mechanize.Browser()
        browser.open(SEARCH_LINK)
        browser.select_form(nr=6)
        browser.form['slowa'] = text
        browser.submit()
        
        source = browser.response().read()
        soup = BeautifulSoup(source)

        try:
            link = MAIN_PAGE + soup.find('td', attrs={"class": 'n'}).a['href']
        except TypeError:
            irc.reply("Sorry, but nothing could be found. Did you type your keywords correctly?")
            return None
            
        try:
            hits = soup.find('tr', attrs={"class": 'list'}).findAll('a')[4].contents[0]
        except IndexError:
            hits = NA

        browser.open(link)
        source = browser.response().read()
        soup = BeautifulSoup(source)

        name = soup.find('h1', attrs={"itemprop": 'name'}).contents[0]
	brand = soup.find('a', attrs={"class": 'brand'}).span.contents[0]
        rate = float(soup.find('abbr', attrs={"itemprop": 'ratingValue'}).contents[0])
        reviews = soup.find('abbr', attrs={"itemprop": 'reviewCount'}).contents[0]
	details = soup.find('span', attrs={"itemprop": 'description'}).contents

        # The longest string contains the description 
	try:
	    desc = max(details, key=len)
	    plaindesc = unidecode(desc)
	except TypeError:
	    desc = NA
            plaindesc = desc

        # Filter out the price and gather the number from a tuple
	try:
            price = NA
            for i in details:
                i = str(i)
                tag = re.search("[C,c]ena:\s*(\d+([\,\.]\d{1,2})?)", i)
                if tag:
                    tuples = tag.groups()
                    tuples = filter(None, tuples)
                    tuples = list(tuples)
                    price = tuples[0]
        except TypeError:
            price = RED + 'error'

        # Extra link to a product image, unhash if you prefer to have it in the search results
	#img = soup.find('a', attrs={"id": 'p'})['href']
	#imglink = 'http:' + re.findall(r"'(.*?)'", img, re.DOTALL)[0]
	stars = self._tenstars(rate)
        starbar = ''.join(stars)

        # It is ugly indeed, but will be changed to a function soon
	information =   PINK + BOLD + 'WIZAZ' + \
		        WHITE + '.PL' + RA +\
		        GREEN + ' Name: ' + RA + name + ' | ' + \
		        TC + 'Brand: ' + RA + brand + ' | ' + \
                        TC + 'Rating: ' + RA + str(rate) + '/5 ' + starbar + ' | ' + \
                        TC + 'My Fav: ' + RA + hits + ' | ' + \
                        TC + 'Reviews: ' + RA + reviews + ' | ' + \
		        TC + 'Price: ' + RA + price + ' zl' + ' | ' + \
		        TC + 'Link: ' + RA + link[:-7] + ' | ' + \
                        TC + 'Desc: ' + RA
    
        # Bot shatters the text leaving bad newline sign
        description = RA + plaindesc[1:]

        irc.reply(information)
        irc.reply(description)

    wizaz = wrap(wizaz, ['text'])

Class = Wizaz

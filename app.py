
from vss_python_api import ApiDeclarations
from datetime import datetime
from flask import Flask, render_template
from dotenv import dotenv_values
import os
import random
import sys
import requests
import re
from bs4 import BeautifulSoup

import portfolio

app = Flask(__name__)

config = {
    **dotenv_values(".env"), 
    **os.environ, 
}

try:
    url = config["VisionectServer"]
    apiKey = config["VisionectApiKey"]
    apiSecret = config["VisionectApiSecret"]
    uuid = config["VisionectUUID"]
except KeyError:
    print (f"You must create a .env file in this directory containing the keys 'VisionectServer', 'VisionectApiKey', 'VisionectApiSecret', and 'VisionectUUID'.")
    sys.exit(1)

print(f"Visionect Server: {url}")
print(f"UUID: {uuid}")

host = "192.168.50.151"
serverPort = 5000

vssApi = ApiDeclarations(url, apiKey, apiSecret)

def getBattery(uuid):
    statusCode, jsonResponse = vssApi.get_device(uuid)
    status = jsonResponse['Status']
    return status['Battery']

@app.route('/finance')
def finance():
    pf = portfolio.getPortfolio()
    total = sum([pf[x]['value'] for x in pf])
    return render_template("finance.html", p=pf, total="${:,.2f}".format(total) )

@app.route('/cards')
def cards():
    pf = portfolio.getPortfolio()
    total = sum([pf[x]['value'] for x in pf])
    smaller = { key: value for key, value in pf.items()}
    return render_template("cards.html", p=smaller, total="${:,.2f}".format(total) )


def findInfobox(soup, classesToLookFor):
    for c in classesToLookFor:
        i = soup.findAll("table", {"class":c})
        if len(i) == 1:
            return i[0]

    return None

@app.route('/quote')
def quote():
    resp = requests.get(url="https://zenquotes.io/api/quotes")    
    if resp:
        data = resp.json()
        data = list(filter(lambda x : "Proverb" not in x['a'], data))
        which = random.choice(data)
    else:
        print(f"Got a bad response: {resp}, data: {resp.data}")
        which = { "q": "An apple a day", "a": "Some lameo" }

    authorInfo = None
    occupation = None
    born = None
    died = None

    authorName = which['a']
    wikipediaUrl = f"http://en.wikipedia.org/wiki/{authorName.replace(' ','_')}"
    htmlContent = requests.get(wikipediaUrl).text
    soup = BeautifulSoup(htmlContent, "lxml")

    # The firstHeading - of which there should be just one - will have the name of the person
    # in it.  This is what I'm using to confirm that I got a good page.
    confirm = soup.findAll(id = "firstHeading")
    if len(confirm) > 0 and confirm[0].text == authorName:
        print(f"Found the right wikipedia page; url: {wikipediaUrl}")
        i = findInfobox(soup, ["infobox biography vcard", "infobox vcard", "infobox"])
        if i != None:
            print(f"Got the infobox information; i: {i}")
            authorInfo = str(i)
            table3 = i.find_all('tr')
            for t in table3:
               th = t.find_all("th")
               data = t.find_all("td")
               if len(th) > 0 and len(data) > 0:
                   v = data[0]
                   if th[0].text == "Born":
                     born = str(v)
                   if th[0].text == "Died":
                     died = str(v)
                   if th[0].text == "Occupation":
                     occupation = str(v)

        print( f"Occupation: {occupation}, born: {born}, died: {died}")
    else:
        print(f"Did not get the correct wikipedia page; url: {wikipediaUrl}")

    faceUrl = f"https://zenquotes.io/img/{authorName.lower().replace(' ','-').replace('.', '_')}.jpg"
    faceResponse = requests.head(faceUrl)
    if faceResponse.status_code != 200:
        print(f"Unable to fetch face Url: {faceUrl}")
        faceUrl = None

    return render_template("quote.html", quote=which['q'], author=authorName, occupation=occupation, born=born, died=died, face=faceUrl)


def filterEntries(entries, toBeRemoved):
    result = []
    for e in entries:
        keep = True
        for r in toBeRemoved:
            if r in e['text']:
                keep = False
        if keep:
            result.append(e)
    return result

def augmentEntry(entries, key, fn):
    for e in entries:
        e[key] = fn(e)

def extractBirthYear(x):
   reg = re.compile('\(b[ c.]*([0-9][0-9]*)\)')
   result = reg.search(x['text'])
   print (f"Looking at {x['text']}")
   if result and result.group(1) != None: 
       return int(result.group(1))
   else:
       return 0

def extractText(l):
    result = []
    for x in l:
        t = x['text']
        result.append(re.sub('&#91;.*&#93;', '', t)) 
    return result

def day(m,d):
    url = f"https://today.zenquotes.io/api/{m}/{d}"
    resp = requests.get(url=url)
    if not resp:
        print(f"Got a bad response: {resp}, data: {resp.data}, status code: {resp.status_code}")
        return render_template("today.html")

    print(f"Got back a response;  url: {url}")
    data = resp.json()
    eventResults = data['data']['Events']
    deathResults = data['data']['Deaths']
    birthResults = data['data']['Births']

    # Some things just don't interest me.
    thingsIdontCareAbout = ["football", "baseball", "Chinese", "Kosovo", "Spanish"]
    birthResults = filterEntries(birthResults, thingsIdontCareAbout)
    deathResults = filterEntries(deathResults, thingsIdontCareAbout)

    print( f"After filter, all birthResults results; len: {len(birthResults)}")
    print( f"After filter, all deathResults results; len: {len(deathResults)}")

    # Find all birthResults that are near my birthday
    augmentEntry(birthResults, "year", lambda x: int(re.sub('&#8211;.*', '', x['text'])))
    augmentEntry(birthResults, "differenceYear", lambda x: abs(1973-x['year']))
    birthResults = sorted(birthResults, key=lambda x: int(x['differenceYear']))
    births = birthResults[0:4]
    print( f"Final births")
    births = sorted(births, key=lambda x: int(x['year']))
    for e in births:
        print( f"  Year: {e['year']}, differenceYear: {e['differenceYear']}, text: {e['text']}")

    # Find all deathResults where the person was born near my year. 
    augmentEntry(deathResults, "year", lambda x: int(re.sub('&#8211;.*', '', x['text'])))
    augmentEntry(deathResults, "bornYear", extractBirthYear)
    augmentEntry(deathResults, "differenceYear", lambda x: abs(1973-x['bornYear']))
    deathResults = sorted(deathResults, key=lambda x: int(x['differenceYear']))
    deaths = deathResults[0:4]
    print( f"Final deaths")
    deaths = sorted(deaths, key=lambda x: int(x['year']))
    for e in deaths:
        print( f"  Year: {e['year']}, bornYear: {e['bornYear']}, differenceYear: {e['differenceYear']}, text: {e['text']}")

    events = extractText(eventResults[-3:])
    deaths = extractText(deaths)
    births = extractText(births)

    return render_template("today.html", month=m, day=d, events=events, deaths=deaths, births=births)

@app.route('/today/')
def today():
    n = datetime.now()
    return day(n.month, n.day)
    
@app.route('/day/<m>/<d>')
def specificDay(m,d):
    return day(m,d)


@app.route('/jumble')
def jumble():
    # Read in my words file.  This assumes that each line has its own word.
    # Then group the words based on 'difficulty'.  I'm simply using the length
    # of the word as a metric here although more complicated ones are clearly
    # possible.
    lines = open('common_words.txt').read().splitlines()
    smallWords = list(filter(lambda x : len(x)==4, lines))
    mediumWords = list(filter(lambda x : len(x)==5, lines))
    longWords = list(filter(lambda x : len(x)==6, lines))
    longLongWords = list(filter(lambda x : len(x)==7, lines))

    words = random.choices(smallWords, k=1)
    words.extend(random.choices(mediumWords, k=2))
    words.extend(random.choices(longWords, k=2))
    words.extend(random.choices(longLongWords, k=1))

    shuffledWords = []
    for w in words:
        lw = list(w.upper())
        random.shuffle(lw)
        print (f"random word: {w}, shuffled: {lw}")
        shuffledWords.append(lw)

    return render_template("jumble.html", words=shuffledWords)

@app.route('/hello')
def helloWorld():
    statusCode, jsonResponse = vssApi.get_device(uuid)

    print (f"Got jsonResponse; type: {jsonResponse}, value: {jsonResponse}")
    display = jsonResponse['Displays'][0]

    print (f"Got displays; type: {type(display)}, value: {display}")

    width = display['Width']
    height = display['Height']

    print (f"Got data; width: {width}, height: {height}")

    status = jsonResponse['Status']

    print (f"Got status; type: {type(status)}, value: {status}")

    battery = status['Battery']
    drain = status['BatteryCurrent']
    voltage = status['BatteryVoltage']

    result = "<p>Hello, World!</p>"

    currentTime = datetime.now().strftime("%H:%M:%S")
    result += f"<BR>Time: {currentTime}</BR>"

    result += f"<BR>width: {width}, height: {height}</BR>"
    result += f"<BR>Battery: {battery}</BR>"
    result += f"<BR>Drain: {drain}</BR>"
    result += f"<BR>Voltage: {voltage}</BR>"

    return result

@app.route('/clock')
def index():
    return render_template("clock.html")

@app.route('/push/<p>')
def push(p):
    url = f"http://{host}:{serverPort}/{p}"
    status, session = vssApi.get_session(uuid)

    if status != 200:
        print(f"Got back unexpected status for get_session: {status}")

    # Set the URL to be the passed in argument
    session["Backend"]["Fields"]["url"] = url

    status = vssApi.update_session(uuid, session)
    if status != 204:
        print(f"Got back unexpected status for update_session: {status}")

    status = vssApi.restart_session(uuid)
    if status != 204:
        print(f"Got back unexpected status for restart_session: {status}")

    return f"Instructing device to fetch url: {url}"

if __name__ == '__main__':
    app.run(debug=True, host=host, port=serverPort)


from vss_python_api import ApiDeclarations
from datetime import datetime
from flask import Flask, render_template
from dotenv import dotenv_values
import os
import random
import sys
import requests
import re

import portfolio
import today
import quote

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

@app.route('/quote')
def quotePage():
    return quote.page()

@app.route('/today/')
def todayPage():
    n = datetime.now()
    return today.day(n.month, n.day)
    
@app.route('/day/<m>/<d>')
def specificDay(m,d):
    return today.day(m,d)


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

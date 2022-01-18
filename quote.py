
from flask import render_template
from bs4 import BeautifulSoup

import requests
import random

def findInfobox(soup, classesToLookFor):
    for c in classesToLookFor:
        i = soup.findAll("table", {"class":c})
        if len(i) == 1:
            return i[0]

    return None

def page():
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


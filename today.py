
import countries
import re
import requests

from flask import render_template

def filterEntries(entries, toBeRemoved):
    result = []
    for e in entries:
        keep = True
        for r in toBeRemoved:
            r = r.lower()
            if r in e['text'].lower():
                keep = False
        if keep:
            result.append(e)
    return result

def augmentEntry(entries, key, fn, errorFn = lambda: 1000 ):
    for e in entries:
        try:
            e[key] = fn(e)
        except:
            e[key] = errorFn()

def extractBirthYear(x):
   reg = re.compile('\(b[ c.]*([0-9][0-9]*)\)')
   result = reg.search(x['text'])
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

    print( f"Prior to all filters; birthResults: {len(birthResults)}, deathResults: {len(deathResults)}")
    birthResults = filterEntries(birthResults, countries.countriesIDontCareAbout)
    deathResults = filterEntries(deathResults, countries.countriesIDontCareAbout)
    birthResults = filterEntries(birthResults, countries.countriesIDontCareAbout)
    deathResults = filterEntries(deathResults, countries.countriesIDontCareAbout)

    # Some things just don't interest me.
    thingsIdontCareAbout = ["football", "baseball", "greek", "french", "canadian",
            "ukrainian", "german", "belgian", "Swedish", "Scottish", "Malayalam", "English",
            "Norwegian", "Dutch", "Finnish", "Turkish",
            "Palestinian", "Spanish", "Mexican", 
            "Italian", "Kosovo", "Welsh", "Czech", "Swiss", 
            "British", "Filipino", "Taiwanese", "Portuguese",
            "Danish", "Bishop of" 


            ]

    birthResults = filterEntries(birthResults, thingsIdontCareAbout)
    deathResults = filterEntries(deathResults, thingsIdontCareAbout)

    print( f"After filtering out things I don't care about; birthResults: {len(birthResults)}, deathResults: {len(deathResults)}")

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
    augmentEntry(deathResults, "year", lambda x: int(re.sub('&#8211;.*', '', x['text']), lambda: 10000))
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


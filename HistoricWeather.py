# See HistoricWeather.pynb for details
# coding: utf-8

# # Download weather data
# Data source http://www.timeanddate.com/weather <br>
# Since the source data mentions a copyright, it is not reproduced. All figures are are calculations in the final function are based on interpolations.
# ## Notes
# This function works for any town and country for which data is available on the timeanddate website. If successful, it returns a five-element list of tuples. The first row contains a tuple of headers ('Date', 'Period', 'Description', 'Temp C', 'TempLow C', 'Pressure mbar', 'WindSpeed mph', 'WindDirn', 'Humidity'). The four remaining entries provide the historic weather observations for four six hour periods during the day. The main periods of interest are morning and afternoon: '06:00 — 12:00' and '12:00 — 18:00'. If unsuccessful, the function prints "No historic data", probably due to the town/country not being in the database or the date being to far back in history.

import urllib.request
import re
import datetime
import pandas as pd


# # Scrape weather in JSON format
# This should be just a case of using a simpler different regular expression. Let's adjust the function using a different regular expression that spots the date and pulls in the rest of the data up to the next curly bracket
# 


def historicWeather(d=29, m=6, y=2015, town='', country='', lat='', lon=''):
    """ Returns (up to) 4 historic weather observations for date, location and country, as a list in JSON format
    Note that pressure is in mbar, wind is in mph with direction as a bearning"""

    locStr = '@' + str(lat) + ',' + str(lon) if (town=='') and (country=='') else country.lower()+'/'+town.lower()
    
    tday = datetime.date.today()
    yday = tday - datetime.timedelta(days=1)

    if datetime.date(y,m,d) in [tday, yday]:    # Different link if date is today or yesterday
        link = 'http://www.timeanddate.com/weather/'+ locStr +'/historic'
    else:
        link = 'http://www.timeanddate.com/weather/'+ locStr +'/historic?month=' + str(m) + '&year=' + str(y)

    # Date padded with an initial space to prevent "15 Jan" and "25 Jan" being picked up by " 5 Jan"
    #dateString = datetime.date(y,m,d).strftime("%A, X%d %B %Y").replace('X0','X ').replace('X','')
    dateString = datetime.date(y,m,d).strftime("%A, X%d %B %Y").replace('X0','').replace('X','')

    try:
        f = urllib.request.urlopen(link)
        myfile = f.read().decode("utf-8")
        f.close()

        # Regular express extracts, date, time period, description, temp, lowtemp, pressure, windSpeed, windDirn and humidity
        pattern = '("ts":"\d{2}:00","ds":"' + dateString + '[^\}]*\})'
        match = re.findall(pattern, myfile[:])
        match = ['{'+m for m in match]
    except:
        match = []
        
    if len(match)==0 :
        print('No historic data available for '+dateString)
        
    return '['+','.join(match)+']'


# # Pull weather into a pandas DataFrame
# Pandas is the most useful format for doing interpolation. Also need to work out what we mean by interpolation for wind direction that changes from 20 to 200, as reported for  11/11/16 in London. We are assuming the observation is an average for the next 6 hours, so interpolation will be using 03:00, 09:00, 15:00, 21:00.

def readWeather(weather,y,m,d):
    dstr = '{:d}-{:02d}-{:02d} '.format(y,m,d)
    try:
        obs = pd.read_json(weather)
        obs.index = pd.DatetimeIndex([dstr+i for i in obs.ts])
        obs.index = obs.index + pd.DateOffset(hours=3)
        obs.drop(['desc','icon','ts','ds','templow'], axis=1, inplace=True)
    except:
        obs = pd.DataFrame({'baro':1020,'hum':80,'temp':15,'wd':0,'wind':0},index=[dstr + "03:00:00"])
    obs.columns = ['Pressure','Humidity','Temp','WindDirn','Wind']
    return obs


# ## Function to interpolate between weather observations, including dealing with messy edge cases

def currentObs(eventDatetime, obs):
    # First calculate ideal weighting vector that will work in the vast majority of cases
    dTime = eventDatetime - datetime.datetime(eventDatetime.year,eventDatetime.month,eventDatetime.day,3,0,0) 
    [Tperiod, Tproportion] = [int((dTime.total_seconds()/3600)//6), (dTime.total_seconds()/3600)%6/6]
    # Set up ideal weighting vector
    w = [0,0,0,0]
    if Tperiod == -1:
        w = [1,0,0,0]
    elif Tperiod == 3:
        w = [0,0,0,1]
    else:
        w[Tperiod] = 1-Tproportion
        w[Tperiod+1] = Tproportion
    
    # Now incorporate a whole load of error handling for incomplete observations, particularly those for today.
    if len(obs) > 0:
        if len(obs) == 1:
            e = obs.iloc[0]
        elif len(obs) == 2:
            if w[0] == 0:
                e = obs.iloc[1]
            else:
                e = w[0]*obs.iloc[0] + w[1]*obs.iloc[1]
                # Wind adjustment
                if abs(obs.iloc[0].WindDirn-obs.iloc[1].WindDirn)>180:
                    e.WindDirn = (e.WindDirn + w[1]*360)%360
        elif len(obs) == 3:
            if w[3] > 0:
                e = obs.iloc[2]
            else:
                e = w[0]*obs.iloc[0] + w[1]*obs.iloc[1] + w[2]*obs.iloc[2]
                # Wind adjustment
                if w[0]:
                    if abs(obs.iloc[0].WindDirn-obs.iloc[1].WindDirn)>180:
                        e.WindDirn = (e.WindDirn + w[1]*360)%360
                else:
                    if abs(obs.iloc[2].WindDirn-obs.iloc[1].WindDirn)>180:
                        e.WindDirn = (e.WindDirn + w[1]*360)%360
        else:
            e = w[0]*obs.iloc[0] + w[1]*obs.iloc[1] + w[2]*obs.iloc[2] + w[3]*obs.iloc[3]
            # Wind adjustment
            if w[0]:
                if abs(obs.iloc[0].WindDirn-obs.iloc[1].WindDirn)>180:
                    e.WindDirn = (e.WindDirn + w[1]*360)%360
            elif w[1]:
                if abs(obs.iloc[2].WindDirn-obs.iloc[1].WindDirn)>180:
                    e.WindDirn = (e.WindDirn + w[1]*360)%360
            else:
                if abs(obs.iloc[2].WindDirn-obs.iloc[3].WindDirn)>180:
                    e.WindDirn = (e.WindDirn + w[2]*360)%360
        e.name = eventDatetime
        e = e.round(0)
    return e


# # Final complete function
# Take a date and a place, return weather observations.<br>
# We can run it over a range of dates and times and store the results in a dataframe.
# 

def weatherObs(d=29, m=6, y=2015, h=14, mi=11, s=20, town='', country='', lat=0, lon=0):
    T = datetime.datetime(y,m,d,h,mi,s)
    weather = historicWeather(d=d, m=m, y=y, town=town, country=country, lat=lat, lon=lon)
    obs = readWeather(weather,y=y,m=m,d=d)
    return currentObs(T,obs)




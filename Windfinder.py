
# coding: utf-8

# # Historic wind directions
# Scrape data from neat graphic on windfinder.com 

# In[198]:

import urllib.request
import re
import pandas as pd

def historicWind(location='london-heathrow'):
    """ Returns historic wind direction chart"""

    address = 'https://www.windfinder.com/windstatistics/'+location
    f = urllib.request.urlopen(address)
    myfile = f.read().decode("utf-8")
    f.close()
    
    # find the relevant part of the html code
    cut = myfile[myfile.find("var options = {\n  chart:"):]
    cut = cut[:cut.find('};')]+'}'
    cut=cut.replace('\n','')
    cut=cut.replace(' ','')
    
    # after hours of messing around, find a regular expression that works
    pattern = r"name:'([a-zA-Z]+)',data:\[([(\d+.\d+),]*)"
    match = re.findall(pattern, cut)
    
    # stick it in a dataframe
    historicWindDirn = pd.DataFrame()
    for m in match:
        historicWindDirn[m[0]] = [float(i) for i in m[1].split(',')]
    historicWindDirn['Bearing'] = pd.Series(range(16))*360/16

    return historicWindDirn


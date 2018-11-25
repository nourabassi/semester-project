import re
import pandas as pd
import os
import sys
import json
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, dest='path', default='data/papers/',  help='specifies the path to input dir')

rootdir = parser.parse_args().path

######################FUNCTIONS

def get_school_from_mail(mail, mapping):
    """maps email to institution"""
    if mail in mapping:
        return (mapping[mail], mail)
    elif re.findall('[a-zA-Z0-9\-]*\.[a-zA-Z0-9\-]*$', mail)[0] in mapping:
        double = re.findall('[a-zA-Z0-9\-]*\.[a-zA-Z0-9\-]*$', mail)[0]
        return (mapping[double], double)
    else:
        triplet = re.findall('[a-zA-Z0-9\-]*\.[a-zA-Z0-9\-]*\.[a-zA-Z0-9\-]*$', mail)
        if len(triplet) > 0 and triplet[0] in mapping:
            return (mapping[triplet[0]], triplet[0])
        else:
            return (np.nan, mail)

def get_org_name(x):
    candidates = x.split('.')
    for c in candidates:
        if c in ['qq','sina','163']:
            return c
    lengths = np.array([len(z) for z in candidates])
    return candidates[lengths.argmax()]

#############################
contents = []
i = 0
source = []
for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        if 'txt' in file:
            i += 1
            path = os.path.join(subdir, file)
            with open(path) as file:
                try:
                    text = file.read()
                    contents.append(text)
                    source.append(path[len(rootdir):-4])
                except:
                    name, message, content = sys.exc_info()
                    print(message)

schools = open('data/world_universities_and_domains.json').read()
parsed_json = json.loads(schools)


mapping = {}
country_uni = {}
for j in parsed_json:
    mapping[j['domains'][0]] = j['name']
    country_uni[j['domains'][0]] = j['country']
    if len(j['domains']) > 1:
        mapping[j['domains'][1]] = j['name']
        country_uni[j['domains'][1]] = j['country']
    if len(j['domains']) > 2:
        mapping[j['domains'][2]] = j['name']
        country_uni[j['domains'][2]] = j['country']


mapping['nie.edu.sg'] = "National Institute of Education (NIE), Singapore"
mapping['rub.de'] = "Ruhr-University Bochum"
mapping['uni-due.de'] = "Universität Duisburg-Essen"
mapping['collide.info'] = "Universität Duisburg-Essen"
mapping['dawsoncollege.qc.ca'] = "Dawson College"
mapping['dawsoncollege.ca'] = "Dawson College"
mapping['johnabbott.qc.ca'] = "John Abbott College"
mapping['johnabbott.ca'] = "John Abbott College"
mapping['vaniercollege.qc.ca'] = 'Vanier Colleege'

institution = []
for text in contents:
    mails_in_paper = re.findall('[a-zA-Z0-9\.\-]*@[a-zA-Z0-9\.\-]*\.[a-zA-Z0-9\.\-]*(?!\S*\:\S*)', text)
    institution.append([(get_school_from_mail(m.split('@')[1].lower(), mapping), m, i) for i, m in enumerate(mails_in_paper)])

inst = pd.DataFrame([(i[0][0],i[0][1], i[1],i[2], source[index]) for index, uni in enumerate(institution) for i in uni ],
                    columns=['name', 'domain', 'mail','authorindex','file'])
inst.loc[inst['name'].isna(),'name'] = inst[inst['name'].isna()].domain.map(lambda x: get_org_name(x))
inst['country'] = inst.domain.map(country_uni)

countries = open('data/country-by-domain-tld.json').read()
parsed_countries = json.loads(countries)
parsed_countries = { parsed['tld']: parsed['country'] for parsed in parsed_countries}

parsed_countries['.uk']= "United Kingdom"
parsed_countries['.us']  = "United States"

inst.loc[inst.country.isna(), 'country'] = inst[inst.country.isna()].domain.map(lambda x: re.findall("(\.[a-zA-Z0-9]*$)",x)[0]).map(parsed_countries)
inst.loc[(inst.country.isna()) & (inst.name.isin(['qq','sina','163'])), 'country'] = 'China'


print('[Info] Saved universities data to ../data/Universities.csv')
inst.to_csv('data/Universities.csv')

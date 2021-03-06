from lxml import etree
import json
import pandas as pd
import os
import dateutil.parser
import argparse
import re
import regex
import numpy as np
import unicodedata
import networkx as nx
import difflib
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, dest='path', default='papers-import/',  help='specifies the path to input dir')
parser.add_argument('-o', type=str, dest='output', default='data/',  help='specifies the path to output dir')

rootdir = parser.parse_args().path
output = parser.parse_args().output


##Functions for parsing

def parse(file_path):
    i = 0
    tmp = ''
    key = ''
    xml2 = etree.iterparse(file_path, recover=True)
    data = []
    for action, elem in xml2:
        data.append((elem.attrib, elem.tag, elem.text))
    data_dict = {}

    for attrib, tag, text in data:
        try :
            tmp = key

            key = attrib.get('qualifier')
            element = attrib.get('element')

            #way to distinguish eliminate some nan!
            if key == 'none':
                key = element

            if key in data_dict.keys() :
                i = i + 1
                data_dict[key + str(i)] = text
            else :
                i = 0
                data_dict[key] = text

        except TypeError:
            if 'subject' in tag:
                if 'subject' in data_dict.keys():
                    data_dict['subject'].append(text)
                else:
                    data_dict['subject'] = [text]

        #parse irregular files
        if 'subject' not in data_dict.keys():
            f = open(file_path)
            text = f.read()
            data_dict['subject'] = regex.findall('&gt;([\w\-\ \;]*)&lt;', text)
            if len(data_dict['subject']) == 1:
                data_dict['subject'] = regex.split(';', data_dict['subject'][0])

    return data_dict

def convert(arg):
    try :
        arg = dateutil.parser.parse(arg)
    except TypeError:
        arg = arg
    return arg

def extract_author(text):
    author_split = r'([\p{L}\-]*[\,] [\p{L}\.\ \-]*[\&\,\.]?)'
    author_split_2 = r'([\p{L}\-\.\ ]* [\p{L}\. \ \-]*[\,\.]?)'
    text =  unicodedata.normalize('NFC', text)
    if regex.match('^([\p{L}\ \-]*\p{Lu}\.\,)', text):
        split = [a.replace(',', '').replace('&', '').rstrip() for a in regex.findall(
            author_split_2, text[:text.find('(')])]
        return split
    else:
        split = [a.replace(',', '').replace('&', '').rstrip() for a in regex.findall(author_split, text[:text.find('(')])]
        tmp = []
        if len(split) == 1:
            return split

        for f, s in zip(split[1:], split[:-1]):
            if len(s) == 1:
                tmp.append(f + s )
            else:
                tmp.append(s)
                tmp.append(f)

        if len(split) == 0:
            return [a.replace(',', '').replace('&', '').rstrip() for a in regex.findall(
            author_split_2, text[:text.find('(')])]

        if len(tmp) == 0:
            return split
        return tmp



def get_authors_month(sentence, debug = False):
    general = r'[\p{L}\,\ \.\:\;\/\&\-\'\`\(\)\’\–\¨\…\‐\*\´\＆\\]*\([\,\ \p{L}\d\-]*(18|19|20)\d{2}[\,\ \p{L}\d\-]*\)'
    match_bad_year = r'[\S\s]*\((18|19|20)\d{2}\/(18|19|20)\d{2}\)'

    match_press = r'[\S\s]*\((i|I)n (P|p)ress|manuscript under review\)'
    match_forth = r'[\S\s]*\((f|F)orthcoming\)'
    match_accepted = r'[\S\s]*\((a|A)ccepted\)'
    match_submitted = r'[\S\s]*\((s|S)ubmitted\)'
    match_underreview = r'[\S\s]*\((u|U)nder (R|r)eview\)'

    sentence =  unicodedata.normalize('NFC', sentence)
    if regex.match(general, sentence):
        s = regex.search(general, sentence).group(0)
        if len(s) > 9:
            return s
    elif re.match(match_bad_year, sentence):
        return re.search(match_bad_year, sentence).group(0)
    elif re.match(match_press, sentence):
        return re.search(match_press, sentence).group(0)
    elif re.match(match_forth, sentence):
        return re.search(match_forth, sentence).group(0)
    elif re.match(match_accepted, sentence):
        return re.search(match_accepted, sentence).group(0)
    elif re.match(match_submitted, sentence):
        return re.search(match_submitted, sentence).group(0)
    elif re.match(match_underreview, sentence):
        return re.search(match_underreview, sentence).group(0)

    return np.nan


def author_title(x):
    """Gets author and tite part of reference string"""
    ref = x
    authors = get_authors_month(x)
    if isinstance(authors, float):
        return None

    search = len(authors)+1

    end = re.search('\.|\?|In Looi', ref[search:])
    if end:
        end = end.start()
    else:
        end = 0
    return ref[: (search+end)]

###MAIN CODE ####

all_data = {}
i= 0
for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        path = os.path.join(subdir, file)
        if 'dublin_core' in (path) :
            i += 1
            num_doc = path[len(rootdir):-4]
            if num_doc in all_data.keys():
                all_data[num_doc+'_'] = parse(path)
            else :
                all_data[num_doc] = parse(path)

print('[INFO] Got data from {} files'.format(i))

df_data = pd.DataFrame(list(all_data.values()), index=all_data.keys())
df_data['available'] = df_data['available'].apply(lambda x : convert(x))
df_data['accessioned'] = df_data['accessioned'].apply(lambda x : convert(x))


cleaning = df_data.reset_index().melt(id_vars=['index','subject', 'iso', 'uri','type','publisher','title', 'issued', 'accessioned', 'citation', 'available', 'abstract'])
cleaning = cleaning[cleaning.value.notna()]
cleaning = cleaning[cleaning.variable.notna()]
cleaning = cleaning[cleaning.value.map(lambda x: len(x) > 2)]
cleaning['author_order'] = cleaning.variable.map(lambda x: 0 if len(re.search('\d*$', x).group(0)) == 0 else int(re.search('\d*$', x).group(0)))
del cleaning['variable']

cleaning.reset_index(drop=True, inplace=True)
cleaning['shortend_names'] = cleaning.citation.map(lambda x: re.match(r'[\S\s]*\(\d{4}\)', x, re.U).group(0)).map(lambda x: extract_author(x))
cleaning['shortend_names'] = cleaning.apply(lambda x: x['shortend_names'][x['author_order']], axis=1)
cleaning.rename(columns={'index': 'file', 'value':'long_name'}, inplace=True)

cleaning['file'] = cleaning.file.map(lambda x: x.replace('/', '_')[:-len('/dublin_core')])
cleaning['identifier'] = cleaning.citation.map(lambda x: author_title(x))

names = cleaning.long_name.unique()
pd.Series(names).to_csv(os.path.join(output, 'name_dict.csv'))
print('[Info] Saved list of all names to name_dict.csv' )

d= {}
for i, m in enumerate(names):
    for j, n in enumerate(names):
        if i < j and not 'de' in m:
            y = set([i.lower() for i in regex.split(' |\,', unicodedata.normalize('NFC', m)) if len(regex.sub('\.', '', i)) > 2])
            name = set([i.lower() for i in regex.split(' |\,', unicodedata.normalize('NFC', n)) if len(regex.sub('\.', '', i)) > 2])
            if len(name.intersection(y)) > 1 and n!= m and not ('Lee' in n or 'Lee' in m):
                d[n]= m

cleaning.loc[cleaning['long_name'].isin(d.keys()), 'long_name'] = cleaning.long_name.map(d)
print('[Info] Unified the following names')
pprint(d)

build_graph = cleaning[['long_name', 'shortend_names', 'file']]
build_graph = pd.merge(build_graph, build_graph, on='file')
build_graph = build_graph[build_graph.long_name_x != build_graph.long_name_y]

G = nx.from_pandas_edgelist(build_graph, source='long_name_x', target='long_name_y')

threshold = 0.8
d = dict()
for name in build_graph.long_name_x.unique():
    members = sorted(list(G.neighbors(name)))
    for i, member in enumerate(members):
            for j, member_2 in enumerate(members):
                if i < j:
                    difference = difflib.SequenceMatcher(None, member, member_2).ratio()
                    if difference > threshold:
                        d[member] = member_2

print('[Info] Unified the following names')
pprint(d)

cleaning.loc[cleaning['long_name'].isin(d.keys()), 'long_name'] = cleaning.long_name.map(d)


print('[INFO] Saved to individual authors list: {} as Parsed_metadata.csv'.format(output))
cleaning.to_csv(os.path.join(output, 'Parsed_metadata.csv'))

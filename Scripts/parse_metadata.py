from lxml import etree
import json
import pandas as pd
import os
import dateutil.parser
import argparse
import re
import regex

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

    return data_dict

def convert(arg):
    try :
        arg = dateutil.parser.parse(arg)
    except TypeError:
        arg = arg
    return arg

def extract_author(text):
    #author_split = r'([\p{L}\-]*[\,] [\p{Lu}\.\ \-]+[\&\,\.]?)'
    #author_split_2 = r'([\p{L}\-\.\ ]* [\p{L}\. \ \-]*[\,\.]?)'
    author_split = r'([\p{L}\-]*[\,] [\p{L}\.\ \-]*[\&\,\.]?)'
    author_split_2 = r'([\p{L}\-\.\ ]* [\p{L}\. \ \-]*[\,\.]?)'
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
#del cleaning['author_order']

cleaning['file'] = cleaning.file.map(lambda x: x.replace('/', '_')[:-len('/dublin_core')])

print('[INFO] Saved to individual authors list: {} as Parsed_metadata.csv'.format(output))
cleaning.to_csv(os.path.join(output, 'Parsed_metadata.csv'))

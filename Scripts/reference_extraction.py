import re
import pandas as pd
import os
import numpy as np
import sys
import matplotlib.pyplot as plt
import json
import argparse
import regex as reg

parser = argparse.ArgumentParser()

parser.add_argument('--input', type=str, dest='path', default='data/papers/',  help='specifies the path to input dir')
parser.add_argument('-o', type=str, dest='output', default='data/',  help='specifies the path to output dir')

rootdir = parser.parse_args().path
output = parser.parse_args().output

def author_title(x):
    """Gets author and tite part of reference string"""
    ref = str(x['ref'])
    authors = str(x['ref_parsed'])
    search = len(authors)+1
    end = re.search('\.|\?', ref[search:])
    if end:
        end = end.start()
    else:
        end = 0
    return ref[: (search+end)]


def ref_extraction(text, extract=False):
    """Extracts refrerence section: works well on well formated documents"""
    mention = text.rfind("\nReferences")
    if mention == -1:
        mention = text.lower().rfind(" references")
    if mention == -1:
        mention =  text.lower().rfind("reference")
    #get reference section, account for different spelling
    acknowledgements = max(text.lower().find("acknowledgements"), text.lower().find('acknowledgments'))

    #handle case that acknowlege ments are before references
    if acknowledgements < mention:
        acknowledgements = -1
    ref = text[mention+len("references"):acknowledgements]
    references = re.split(r'\n', ref)

    ref = [r for r in references if r and len(r) > 3 and not re.match(r'(CSCL|ICLS) \d{4} Proceedings|© ISLS', r)]
    if extract:
        print(text[mention+len("references"):acknowledgements])
        print(references)
    return ref

def contains_citation_beginning(sentence):
    """Checks if string begings with an citation (in APA format)"""
    ##Check for mention of publication date,
    #do it this way to not allow for ICLS 2015 string to be counted
    months = '(january|february|march|april|may|june|july|august|september|october|november|december)?'
    publication_year = r'(?<!\d)\('+months+'[\-\ ]*'+months+'[\ \,]*(18|19|20)\d{2}[a-z]?[\,\ ]*'+months+'[\-\ \d]*'+months+'\)'

    #sometimes two years are mentioned, we use this regex to parse them
    match_bad_year = r'\((18|19|20)\d{2}\/(18|19|20)\d{2}\)'

    #these regex account for special strings used in the references
    match_press = r'[\w\ \. \,\&\(\)\-\'\…]*\(in press\)'
    match_forth = r'[\S\s]*\(forthcoming\)'
    match_accepted = r'[\S\s]*\(accepted\)'
    match_submitted = r'[\S\s]*\(submitted\)'
    match_underreview = r'[\S\s]*\(under review\)'
    sentence = sentence.lower()

    year = re.search(publication_year, sentence) or  re.search(match_bad_year, sentence)

    return  year or \
            re.match(match_press, sentence) or re.match(match_forth, sentence) or\
            re.match(match_accepted, sentence) or re.match(match_submitted, sentence) or\
            re.match(match_underreview, sentence)

def moving_up(issues, condition=lambda x: re.match('^[\d\(\.\&\ ]', x)):
    """Attaches sentence followed by sentence satisfying condition to that sentence"""
    issues = [i for i in issues if len(i) > 0]
    patchwork = []
    j = 0

    for i, sentence in enumerate(issues):
        if i != 0 and condition(sentence):
            patchwork[j-1] += ' ' + sentence
        else:
            j +=1
            patchwork.append(sentence)
    patchwork = [p for p in patchwork if len(p) > 0]

    return patchwork

def moving_down(issues, condition=lambda x: re.match('^[\d\(\.]', x)):
    """Moving sentences starting with lowercase letter or number strings "one up" """

    issues = [i for i in issues if len(i) > 0]
    patchwork = issues.copy()
    j = 0

    for i, sentence in enumerate(issues):
        if condition(sentence) and i+1 < len(issues):
            patchwork[i] = sentence + ' ' + patchwork[i+1]
            patchwork[i+1] = ''

    patchwork = [p for p in patchwork if len(p) > 0]

    return patchwork

def match_author(authors):
    """Identifies string starting with authors (APA) format"""

    regex = r'(([\w\-]*[\,\&] [A-Z\.\ ]+[\&\,]?)*$)'
    USA = r'([A-Z]{2,})'
    return not re.search(USA, authors) and re.match(regex, authors)



def get_authors_month(sentence, debug = False):
    regex = r'[ééüş\xad\p{L}\,\ \.\:\;\/\&\-\'\`\(\)\’\–\¨\…\‐\*\´\＆\\]*\([\,\ \p{L}\d\-]*(18|19|20)\d{2}[\,\ \p{L}\d\-]*\)'
    match_bad_year = r'[\S\s]*\((18|19|20)\d{2}\/(18|19|20)\d{2}\)'

    match_press = r'[\S\s]*\((i|I)n (P|p)ress|manuscript under review\)'
    match_forth = r'[\S\s]*\((f|F)orthcoming\)'
    match_accepted = r'[\S\s]*\((a|A)ccepted\)'
    match_submitted = r'[\S\s]*\((s|S)ubmitted\)'
    match_underreview = r'[\S\s]*\((u|U)nder (R|r)eview\)'

    #sentence = sentence.lower()
    if reg.match(regex, sentence):
        s = reg.search(regex, sentence).group(0)
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


def extract_year(x):
    """Returns year of reference"""
    match_press = r'\(in press\)'
    years = r'\([\w\d\,\ \.]*(18|19|20)\d{2}[\,\ \w\d]*\)'
    year = re.search(years, x)
    if re.search(match_press, x):
        return 2018
    if year:
        year = year.group(0)
        year = re.findall('\d{4}', year)
        return int(year[0])
    else:
        return np.nan


#### Main Code
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

references = []
for i, content in enumerate(contents):
    references.append((ref_extraction(content)))

print('\tNumber of pdf documents : ', len(contents))
print('\tNumber of documents for which we have an extracted reference section: ', len(references))


#iteration 1: move up strings that start in number or with (
ref_1 = [moving_up(r) for r in references]
#iteration 2: move up string starting with "Proceedings"
ref_2 = [moving_up(r, lambda x: re.match('^Proceedings', x)) for r in ref_1]

cutoff_name = r'^[A-Z]+\.\ ?'
ref_3 = [moving_up(r, lambda x: re.match(cutoff_name, x)) for r in ref_2]
ref_4 = [moving_down(r, lambda x: match_author(x)) for r in ref_3]
#pivoting up around strings containing citation
ref_5 = [moving_up(r, lambda x: not contains_citation_beginning(x)) for r in ref_4]
#if ends in word
words_at_end = r'\ [a-zA-Z]*$'
ref_6 = [moving_down(r, lambda x: re.search(words_at_end, x)) for r in ref_5]

#build dataframe
references_df = pd.DataFrame([(f, source[i]) for i, flat in enumerate(ref_6) for f in flat], columns=['ref', 'file'])
references_df['ref_parsed'] = references_df.apply(lambda x: get_authors_month(x['ref']), axis=1)

print('\tPercentage of unparsed references: {:0.3f}'.format(references_df.ref_parsed.isna().sum()/references_df.ref_parsed.shape[0]))
print('\tNumber of unparsed references: ', references_df[references_df.ref_parsed.isna()].ref.shape[0])
print('\tNumber of properly parsed references: ', references_df.ref_parsed.shape[0])

references_df.loc[~references_df.ref_parsed.isna(),'year'] = references_df[~references_df.ref_parsed.isna()].ref_parsed.map(extract_year)
references_df['identifier'] = references_df.apply(author_title , axis=1)

print('\tSaved reference list to: {} as References.csv'.format(output))
os.path.join(output, 'References.csv')
references_df.to_csv(os.path.join(output, 'References.csv'))



#extract authors and clean strings a bit
regex = r'([\w\-]*[\,] [A-Z\.\ ]+[\&\,]?)'
references_df['authors'] =  references_df[~references_df.ref_parsed.isna()].ref_parsed.map(lambda x: [a.replace(',', '').replace('&', '').rstrip() for a in re.findall(regex, x)] )

tags = references_df.authors.apply(pd.Series)
tags = tags.rename(columns = lambda x : 'tag_' + str(x))

df = pd.concat([references_df, tags], axis=1)
tag_cols = [c for c in df.columns if 'tag' not in c]
df = df.melt(id_vars=tag_cols)

df['author'] = df['value']
df = df[df.value.notna()].reset_index(drop=True)
del df['variable'], df['authors'], df['value']

print('\tSaved to individual authors list: {} as Reference_authors.csv'.format(output))
df.to_csv(os.path.join(output, 'Reference_authors.csv'))

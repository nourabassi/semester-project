import os
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, dest='path', default='papers-import/',  help='specifies the path to input dir')
parser.add_argument('-o', type=str, dest='output', default='data/papers/',  help='specifies the path to output dir')


rootdir = parser.parse_args().path
output = parser.parse_args().output

print('[Info] Parsing from {}'.format(rootdir))
TOTEXT = 'pdftotext '
PARAMS = ' -nopgbrk -eol mac'

j = 0
for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        path = os.path.join(subdir, file)+' '
        path_out = os.path.join(output, subdir[len(rootdir):].replace('/', '_')+file[file.find('/'):-len('.pdf')]+'.txt')
        if '.pdf' in path:
            j += 1
            os.system(TOTEXT + path + path_out + PARAMS)
            sys.stdout.write("\r[Info] Parsed {} documents, parsing document {}".format(j, path))
            sys.stdout.flush()

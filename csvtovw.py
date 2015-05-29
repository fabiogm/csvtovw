#!/usr/bin/env pypy

# The MIT License (MIT)
# 
# Copyright (c) 2015 Fabio Gabriel
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import csv
import sys
from itertools import chain

class FeatureLine(object):
    def __init__(self, *kwargs):
        self.string_namespace = []
        self.numeric_namespace = []
        self.label = ''


def append_feature_line(feature_line, name, val, typ):
    if typ == 'str':
        feature_line.string_namespace.append((name, val))
    else:
        feature_line.numeric_namespace.append((name, val))

    return feature_line


def create_vw_line(feature_line, bow=False):
    line = ''

    if feature_line.label != '':
        line += feature_line.label
        line += ' |'
    else:
        line += ' |'
   
    if bow:
        for f in feature_line.string_namespace:
            line += ' ' + f[1]

        for f in feature_line.numeric_namespace:
            line += ' ' + f[1]
    
    else:
        for f in feature_line.string_namespace:
            line += ' ' + f[0] + '_' + f[1]

        for f in feature_line.numeric_namespace:
            line += ' ' + f[0] + ':' + f[1]

    return line


def emit(line, f):
    f.write(line)
    f.write('\n')


def infer_types(reader, label):
    fieldtypes = {}
    line = reader.next()

    for k, v in line.iteritems():
        try:
            int(v)
            fieldtypes[k] = 'int'
        except:
            try:
                float(v)
                fieldtypes[k] = 'float'
            except:
                fieldtypes[k] = 'str'

    return line, fieldtypes 


def csv_to_vw(inputfile, outputfile, label, userTypes, bow, ignore):
    with open(inputfile, 'r') as infile, open(outputfile, 'wb') as outfile:
        reader = csv.DictReader(infile)
        l, types = infer_types(reader, label)
        if userTypes:
            types.update(userTypes)

        if not ignore:
            ignore = []

        for line in chain([l], reader):
            line_str = ''
            feature_line = FeatureLine()
            
            for name in reader.fieldnames:
                val = line[name]
    
                # TODO. Clumsy way of converting 0 labels to -1 on training data. Only on binary classification problems, fix it.
                if label and name == label and types[label] == 'int':
                    if val == '0' or val == 0:
                        val = '-1'
                    else:
                        val = '1'

                # TODO. Turn this into an option.
                val = val.replace(' ', '_')

                if name == label:
                    feature_line.label = val
                else:
                    if name not in ignore:
                        feat_line = append_feature_line(feature_line, name, val, types[name])
            
            
            line_str = create_vw_line(feature_line, bow)
            emit(line_str, outfile)


def main(input_file, output_file, separator, namespaces, label, bow, types, ignore):
        csv_to_vw(input_file, output_file, label, types, bow, ignore)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CSV files to Vowpal Wabbit format.')
    parser.add_argument('-l', '--label', type=str, help='Label column, in case this is a train file.') 
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('output_file', help='Path to output Vowpal Wabbit format file')
    parser.add_argument('-s', '--separator', type=str, default=',', help='Field separator. Default , (comma)')
    parser.add_argument('-n', '--namespace', nargs=2, type=str, action='append', help='Specify namespaces.')
    parser.add_argument('-t', '--type', nargs=2, type=str, action='append', help='Specify field type, overriding detection.')
    parser.add_argument('-b', '--bow', action='store_true', help='Use Bag of Words.')
    parser.add_argument('-i', '--ignore', type=str, action='append', help='Ignore fields.')
    args = parser.parse_args()
    main(args.input_file, args.output_file, args.separator, args.namespace, args.label, args.bow, args.type, args.ignore) 


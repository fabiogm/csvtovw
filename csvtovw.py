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
import platform
import sys
from collections import defaultdict
from itertools import chain

printf = None

class FeatureLine(object):
    def __init__(self, *kwargs):
        self.string_namespace = []
        self.numeric_namespace = []
        self.other_namespaces = defaultdict(lambda: [])
        self.label = ''


    def append(self, name, val, typ, namespace):
        if namespace:
            self.other_namespaces[namespace].append((name, val))
        elif typ == 'str':
            self.string_namespace.append((name, val))
        else:
            self.numeric_namespace.append((name, val))


def create_vw_line(feature_line, namespacenames, bow=False):
    line = ''

    if feature_line.label != '':
        line += feature_line.label
        
        if not namespacenames:
            line += ' |'
    #else:
    #    if not namespacenames:
    #        line += ' |'
   
    if bow:
        for f in feature_line.string_namespace:
            line += ' ' + f[1]

        for f in feature_line.numeric_namespace:
            line += ' ' + f[1]

    else:
        if namespacenames:
            for f in feature_line.string_namespace:
                line += ' |' + f[0] + ' ' + f[1]

            line += ' |numeric'
            for f in feature_line.numeric_namespace:
                line += ' ' + f[0] + ':' + f[1]
        
        else:
            for f in feature_line.string_namespace:
                line += ' ' + f[0] + '_' + f[1]

            for f in feature_line.numeric_namespace:
                line += ' ' + f[0] + ':' + f[1]

    for k, v in feature_line.other_namespaces.iteritems():
        line += ' |' + k

        for f in v:
            line += ' ' + f[1]

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


def csv_to_vw(inputfile, outputfile, label, userTypes, namespaces, bow, ignore, namespacenames):
    with open(inputfile, 'r') as infile, open(outputfile, 'wb') as outfile:
        reader = csv.DictReader(infile)
        l, types = infer_types(reader, label)
        
        if not outfile:
            outfile = sys.stdout
        
        if not namespaces:
            namespaces = {}

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
                #if not bow:
                #    val = val.replace(' ', '_')

                if name == label:
                    feature_line.label = val
                else:
                    if name not in ignore:
                        feature_line.append(name, val, types[name], namespaces.get(name))
            
            
            line_str = create_vw_line(feature_line, namespacenames, bow)
            emit(line_str, outfile)


def main(args):
    global printf

    def myprint(x):
        print x

    if args.verbose:
        printf = myprint
    else:
        printf = lambda x: None

    if platform.python_implementation() != 'PyPy':
        printf('Run this through PyPy for better performance')

    printf('Converting %s -> %s' % (args.input_file, args.output_file))
    printf('Separator: %s' % args.separator)
    printf('Bag of Words? %s' % ('Yes' if args.bow else 'No'))
    printf('Ignoring fields: %s' % args.ignore)
    printf('Label: %s' % args.label)

    csv_to_vw(args.input_file, args.output_file, args.label, args.type, dict(args.namespace), args.bow, 
            args.ignore, args.namespacenames)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CSV files to Vowpal Wabbit format.')
    parser.add_argument('-l', '--label', type=str, help='Label column, in case this is a train file.') 
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('output_file', help='Path to output Vowpal Wabbit format file')
    parser.add_argument('-s', '--separator', type=str, default=',', help='Field separator. Default , (comma)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Activate verbose output')
    parser.add_argument('-n', '--namespace', nargs=2, type=str, action='append', help='Specify namespaces.')
    parser.add_argument('-t', '--type', nargs=2, type=str, action='append', help='Specify field type, overriding detection.')
    parser.add_argument('-b', '--bow', action='store_true', help='Use Bag of Words.')
    parser.add_argument('-i', '--ignore', type=str, action='append', help='Ignore fields.')
    parser.add_argument('-nn', '--namespacenames', action='store_true', help='Create separate namespaces for each feature.')
    args = parser.parse_args()
    args.namespace = args.namespace if args.namespace else []
    main(args)


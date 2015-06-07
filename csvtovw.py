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

    def to_vw(self, namespacenames, bow=False):
        line = ''

        if self.label != '':
            line += self.label
            
            if not namespacenames:
                line += ' |'
       
        if bow:
            line = self._append_to_line(line, self.string_namespace, True, False)
            line = self._append_to_line(line, self.numeric_namespace, True, False)

        else:
            if namespacenames:
                line = self._append_to_line(line, self.string_namespace, True, True, ' |') 
                line += ' |numeric'
                line = self._append_to_line(line, self.numeric_namespace, True, True, ' ', ':')
            
            else:
                line = self._append_to_line(line, self.string_namespace, True, True, ' ', '_')
                line = self._append_to_line(line, self.numeric_namespace, True, True, ' ', ':')

        for k, v in self.other_namespaces.iteritems():
            line += ' |' + k

            line = self._append_to_line(line, v, False, True, ' ', '')

        return line
    
    def _append_to_line(self, line, items_col, print_first, print_second, beg=' ', sep=' '):
        for f in items_col:
            line += beg
            line += f[0] if print_first else ''
            line += sep
            line += f[1] if print_second else ''

        return line

    @classmethod
    def from_dict(cls, d, fieldnames, label, types, ignore, namespaces):
        feature_line = cls()
        
        for name in fieldnames:
            val = d[name]

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
        
        return feature_line


def emit(line, f):
    f.write(line)
    f.write('\n')


def infer_types(reader):
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
        l, types = infer_types(reader)
        
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
            feature_line = FeatureLine.from_dict(line, reader.fieldnames, label, types, ignore, namespaces)
            line_str = feature_line.to_vw(namespacenames, bow)
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


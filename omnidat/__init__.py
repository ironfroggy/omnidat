#!/usr/bin/env python3

import sys
import argparse
import re
import shlex
from ast import literal_eval


# Constants

R_KEY = r'([\w\-]+)'
R_DELIM = r'([\^+=:/\\])?'
# quoted or non-quoted values, adapted from
# http://mail.python.org/pipermail/tutor/2003-December/027063.html
R_VALUE = r'((?:"[^"]*\\(?:.[^"]*\\)*.[^"]*")|(?:"[^"]*")|\w+|(?:\'[^\']*\\(?:.[^\']*\\)*.[^\']*\')|(?:\'[^\']*\'))?'

R_DATA = re.compile('{}{}{}'.format(R_KEY, R_DELIM, R_VALUE))


# Command line processing

# why is this needed in Python 3?
import pkg_resources
from straight.command import Command, Option, SubCommand

class Omnidat(Command):
    filename = Option(dest='filename', action='store')

    class List(Command):
        rest = Option(dest='rest', default=list, action='append')

        def execute(self, **extra):
            om = OmFile(self.args.filename)
            for f in self.args.rest:
                key, delim, value = R_DATA.match(f).groups()
                try:
                    value = literal_eval(value)
                except (ValueError, SyntaxError):
                    pass
                if delim == '=':
                    om = om.filter(**{key: value})
                elif delim == '^':
                    om = om.exclude(**{key: value})
            for line in om:
                print_datum(line, [])

    class Add(Command):
        rest = Option(dest='rest', default=list, action='append')

        def execute(self, **extra):
            om = OmFile(self.args.filename)
            data = []
            for f in self.args.rest:
                key, delim, value = f.partition('=')
                assert delim == '=', "Can only add with =, not {}".format(repr(delim))
                try:
                    value = literal_eval(value)
                except ValueError:
                    pass
                except SyntaxError:
                    pass
                data.append({key: value})
            om.add(*data)

    class Trim(Command):
        rest = Option(dest='rest', default=list, action='append')

        def execute(self, **extra):
            print("TRIM not implemented yet")

    class Remove(Command):
        rest = Option(dest='rest', default=list, action='append')

        def execute(self, **extra):
            print("REMOVE not implemented yet")


# Utilities

def print_datum(datum, keys):
    items = list(datum.items())
    if keys:
        items.sort(key=lambda _: keys.index(_[0]))
    if len(keys) > 1 or not keys:
        print(', '.join(': '.join((k, str(v))) for (k, v) in items if not k.startswith('_') or k in keys))
    else:
        print(datum[keys[0]])


# Core

class OmFile(object):

    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                data = self._decode_line(line)
                if data:
                    yield data

    def filter(self, *args, **kwargs):
        return OmFilter(self).filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        return OmFilter(self).exclude(*args, **kwargs)

    def add(self, *data):
        with open(self.filename, 'a') as f:
            for line in data[:-1]:
                f.write(self._encode_line(line))
                f.write(' ')
            f.write(self._encode_line(data[-1]))
            f.write('\n')

    def _encode_line(self, data):
        terms = []
        for (k, v) in data.items():
            terms.extend(self._prepare_pair(k, v))
        return ' '.join(terms)

    def _prepare_pair(self, k, value):
        if isinstance(value, (int, bool, str)):
            yield '{}={}'.format(k, repr(value))
        elif isinstance(value, list):
            for each_value in value:
                yield '{}={}'.format(k, repr(each_value))

    def _decode_line(self, line):
        data = {}
        terms = R_DATA.findall(line)
        for key, delim, value, *_ in terms:
            try:
                value = literal_eval(value)
            except (ValueError, SyntaxError):
                raise ValueError("Cannot parse value %r" % (value,))
            if key in data:
                try:
                    data[key].append
                except AttributeError:
                    data[key] = [data[key]]
                data[key].append(value)
            else:
                data[key] = value
        return data


class OmFilter(object):

    def __init__(self, of, filters=None, excludes=None):
        self.of = of
        self.filters = filters or {}
        self.excludes = excludes or {}

    def _filter_or_exclude(self, src, filter, keys):
        for line in src:
            ok = True
            for k, v in keys.items():
                if filter:
                    if line.get(k) != v:
                        ok = False
                        break
                else:
                    if line.get(k) == v:
                        ok = False
                        break
            if ok:
                yield line

    def __iter__(self):
        filtered = self._filter_or_exclude(self.of, True, self.filters)
        excluded = self._filter_or_exclude(filtered, False, self.excludes)
        return excluded

    def filter(self, **keys):
        return type(self)(self, keys, self.excludes)

    def exclude(self, **keys):
        return type(self)(self, self.filters, keys)
 

if __name__ == '__main__':
    Omnidat().run(sys.argv[1:])

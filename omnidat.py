#!/usr/bin/env python3

import sys
import argparse
import re
import shlex
from ast import literal_eval


parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE')
parser.add_argument('action', metavar='ACTION', default="LIST", nargs="?")

R_KEY = r'(\w+)'
R_DELIM = r'([+=:/\\])?'
# quoted or non-quoted values, adapted from
# http://mail.python.org/pipermail/tutor/2003-December/027063.html
R_VALUE = r'((?:"[^"]*\\(?:.[^"]*\\)*.[^"]*")|(?:"[^"]*")|\w+|(?:\'[^\']*\\(?:.[^\']*\\)*.[^\']*\')|(?:\'[^\']*\'))?'

R_DATA = re.compile('{}{}{}'.format(R_KEY, R_DELIM, R_VALUE))


class OmFile(object):

    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                yield self._decode_line(line)

    def append(self, data):
        with open(self.filename, 'a') as f:
            f.write(self._encode_line(data))
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
            value = literal_eval(value)
            if key in data:
                try:
                    data[key].append
                except AttributeError:
                    data[key] = [data[key]]
                data[key].append(value)
            else:
                data[key] = value
        return data
 

def print_datum(datum, keys):
    items = list(datum.items())
    if keys:
        items.sort(key=lambda _: keys.index(_[0]))
    if len(keys) > 1 or not keys:
        print(', '.join(': '.join((k, str(v))) for (k, v) in items if not k.startswith('_') or k in keys))
    else:
        print(datum[keys[0]])

def main(argv):
    args, rest = parser.parse_known_args(argv[1:])
    return globals()["do_" + args.action.upper()](args, *rest) or 0

def _filter(args, *rest, negate=False):
    rest = list(rest)
    filters = None
    keys = []
    if rest:
        while rest and '=' not in rest[0]:
            keys.append(rest.pop(0))
        filters = dict(item.split('=', 1) for item in rest)
    with open(args.filename) as f:
        for line in f:
            linedata = json.loads(line)
            approved = False
            if filters:
                approved = True
                for fkey, fvalue in filters.items():
                    if linedata.get(fkey) != fvalue:
                        approved = False
            else:
                approved = True
            if negate:
                approved = not approved
            if approved:
                if keys:
                    linedata = dict((k, v) for (k, v) in linedata.items() if k in keys)
                if linedata:
                    yield (linedata, keys)

def _filter_and_save(args, *rest, negate=False):
    keep = []
    for linedata, keys in _filter(args, *rest, negate=negate):
        keep.append(linedata)
    with open(args.filename, 'w') as f:
        for linedata in keep:
            f.write(json.dumps(linedata))
            f.write('\n')

def do_LIST(args, *rest): 
    for linedata, keys in _filter(args, *rest):
        print_datum(linedata, keys)

def do_TRIM(args, *rest):
    _filter_and_save(args, *rest, negate=False)

def do_REM(args, *rest):
    _filter_and_save(args, *rest, negate=True)

def do_ADD(args, *rest):
    rest = list(rest)
    with open(args.filename) as f:
        item_count = len(list(f))
    with open(args.filename, 'a') as f:
        data = {}
        while rest:
            k = rest.pop(0)
            v = rest.pop(0)
            data[k] = v
        data['_id'] = item_count
        f.write(json.dumps(data))
        f.write('\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv))

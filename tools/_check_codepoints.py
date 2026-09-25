import io
import sys

with io.open('../work/trans/strings.tsv', encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if a[0] in ('e2d48271af', '790e9393f8', '92826d9609', 'f653d32d9d', '1a04546560'):
            print('==', a[0])
            print(repr(a[5]))
            for c in a[5]:
                if c == '\\':
                    continue
                print('  %r  U+%04X' % (c, ord(c)))

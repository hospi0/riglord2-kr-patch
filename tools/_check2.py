import io

with io.open('../work/trans/scope_jp.tsv', encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if a[0] in ('59bf24a3cc', 'd98c0a5e1f'):
            print('==', a[0], repr(a[5]))
            for c in a[5]:
                if c == '\\' or c == 'n':
                    continue
                print('  %r U+%04X' % (c, ord(c)))

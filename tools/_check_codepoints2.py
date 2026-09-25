import io

with io.open('../work/trans/scope_jp.tsv', encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if a[0] in ('2bb7f847b9', '3f05a4b1a4', '3d1421847a'):
            print('==', a[0])
            t = a[5]
            i = t.find('（') if '（' in t else t.find('(')
            print(repr(t[:80]))
            for c in t[:60]:
                if c in ('\\', 'n'):
                    continue
                print('  %r U+%04X' % (c, ord(c)))

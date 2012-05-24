def iter_cross(iters):
    if len(iters) == 0:
        yield []
    else:
        for v_first in iters[0]:
            for v_rest in iter_cross(iters[1:]):
                yield [v_first] + v_rest

for vals in iter_cross([xrange(3), xrange(2)]):
    print vals

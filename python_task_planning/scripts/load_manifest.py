import time

t0 = time.time()
import roslib
t1 = time.time()
roslib.load_manifest('hip')
t2 = time.time()

print 'Imported in %f seconds and loaded in %f seconds' % (t1 - t0, t2 - t1)

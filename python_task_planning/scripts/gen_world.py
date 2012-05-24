import roslib; roslib.load_manifest('hip')
import numpy as np
from matplotlib import pyplot as plt
from pr2_python.geom import Transform

from hip.hip_world import HIPWorld
from hip.hip_table import HIPTable
from hip.viz_mpl import VizMPL

NTABLES = 3

world = HIPWorld()
for table_i in range(NTABLES):
    trans = np.array((np.random.random()*10.0, np.random.random()*10.0, 0.8))
    rot = np.array((0.0, 0.0, 0.0, 1.0))
    transform = Transform().from_trans_rot(trans, rot)
    table = HIPTable('table_%d' % table_i, transform, (1.0, 1.0))
    world.add_object(table)
    
viz = VizMPL()
viz.draw(world)
plt.show()

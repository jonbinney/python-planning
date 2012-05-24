import roslib; roslib.load_manifest('hip')
import sys
import numpy as np
from pr2_python.geom import Transform

from hip import Operator, Fluent, ConjunctionOfFluents, HPlanTree
from hip.hplanner import hplan
from hip.dot_graph import dot_from_plan_tree

if __name__ == '__main__':
    if 0:
        w_start = SushiWorld()
        # create table
        trans = np.array((np.random.random()*10.0, np.random.random()*10.0, 0.8))
        rot = np.array((0.0, 0.0, 0.0, 1.0))
        transform = Transform().from_trans_rot(trans, rot)
        table = Table('table', transform, (1.0, 1.0))
        w_start.objects.append(table)
        # create cup and bowl
        trans = np.array((0.0, 0.0, 0.0))
        rot = np.array((0.0, 0.0, 0.0, 1.0))
        transform = Transform().from_trans_rot(trans, rot)
        cup = SushiObject('cup', transform)
        bowl = SushiObject('bowl', transform)
        w_start.objects.append(cup)
        w_start.objects.append(bowl)

    # run the planner
    start_state = ConjunctionOfFluents([])
    world = SushiWorld(start_state)
    goal = ConjunctionOfFluents([TableIsSet(('table',))])

    plan_tree = HPlanTree()
    hplan(operators, start_state, goal, world, tree=plan_tree)
    print tree

    if len(sys.argv) > 1:
        outfile = sys.argv[1]
        f = open(outfile, 'w+')
        f.write(dot_from_plan_tree(plan_tree))
        f.close()
        

import threading
import os.path
import roslib
import rospy
import hip

from hip_sushi import domain as sd

class InteractiveWorldWrapper:
    def __init__(self, world, ex_callback, plan_tree):
        self.__world = world
        self._ex_callback = ex_callback
        self._plan_tree = plan_tree

    def execute(self, op):
        print 'WRAPPER EXECUTING OP: %s' % (str(op),)
        self._ex_callback(op, self._plan_tree)
        rospy.sleep(2.0)
        return self.__world.execute(op)
    
    def entails(self, other):
        return self.__world.entails(other)

class HipViewerNode(threading.Thread):
    def __init__(self, ex_callback):
        threading.Thread.__init__(self)
        self.daemon = True
        self.ex_callback = ex_callback

    def run(self):
        goal = hip.ConjunctionOfFluents([sd.TableIsSet(('table',))])
        self.plan_tree = hip.HPlanTree(goal)

        start_state = hip.ConjunctionOfFluents([])
        world = sd.SushiWorld(start_state)
        interactive_world = InteractiveWorldWrapper(world, self.ex_callback, self.plan_tree)


        hip.hplan(sd.operators, start_state, goal, interactive_world, tree=self.plan_tree)
        print 'Planning done'
        return self.plan_tree
        

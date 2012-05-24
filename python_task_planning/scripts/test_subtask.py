import roslib; roslib.load_manifest('hip')
from hip import SubTask

def cup_suggester(current_state, goal, symbols):
    for x in [1, 2, 3]:
        yield x

def bowl_suggester(current_state, goal, symbols):
    for x in ['a', 'b', 'c']:
        yield x

class PickupObject(SubTask):
    def __init__(self):
        SubTask.__init__(self,
            target = None,
            exists = {'cup':cup_suggester, 'bowl':bowl_suggester},
            preconditions = [],
            side_effects = []
            )


PickupObject().operations(None, None, None, None)

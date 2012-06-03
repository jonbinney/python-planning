import roslib; roslib.load_manifest('python_task_planning')
import sys

import python_task_planning as ptp

######################################################################################################################
# World
######################################################################################################################

class SushiWorld:
    def __init__(self, start_state):
        self.current_state = start_state

    def execute(self, op):
        if not self.current_state.entails(op.preconditions):
            raise RuntimeError('Preconditions dont hold!')

        fluents = list(self.current_state.fluents)
        for f in [op.target] + list(op.side_effects.fluents):
            if not self.current_state.entails(f):
                fluents.append(f)
        self.current_state = ptp.ConjunctionOfFluents(fluents)
        
        return self.current_state

    def entails(self, cof):
        return self.current_state.entails(cof)

######################################################################################################################
# Suggesters
######################################################################################################################

def table_to_set_suggester(world, current_state, goal):
    for f in goal.fluents:
        if f.name == 'TableIsSet':
            yield f._args[0]

def cup_suggester(world, current_state, goal):
    yield ptp.Symbol('cup1')

def bowl_suggester(world, current_state, goal):
    yield ptp.Symbol('bowl1')

def setting_location_suggester(world, current_state, goal):
    yield ptp.Symbol('loc1')
    
######################################################################################################################
# Predicates
######################################################################################################################

TableIsSet = ptp.Predicate('TableIsSet', ['table'])
CupIsSet = ptp.Predicate('CupIsSet', ['cup'])
BowlIsSet = ptp.Predicate('BowlIsSet', ['bowl'])
LocKnown = ptp.Predicate('LocKnown', ['object'])
ObjectAtLoc = ptp.Predicate('ObjectAtLoc', ['object', 'loc'])
ObjectInGripper = ptp.Predicate('ObjectInGripper', ['object'])

######################################################################################################################
# Operators
######################################################################################################################

table = ptp.Variable('table')
cup = ptp.Variable('cup')
bowl = ptp.Variable('bowl')
setting_location = ptp.Variable('setting_location')
SetTable = ptp.Operator(
    'SetTable',
    target = TableIsSet((table,)),
    suggesters = {cup:cup_suggester, bowl:bowl_suggester, setting_location:setting_location_suggester},
    preconditions = [
        (1, CupIsSet((cup, setting_location))),
        (1, BowlIsSet((bowl, setting_location)))],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive = False
    )

cup = ptp.Variable('cup')
setting_location = ptp.Variable('setting_location')
SetCup = ptp.Operator(
    'SetCup',
    target = CupIsSet((cup, setting_location)),
    suggesters = {},
    preconditions = [
        (1, LocKnown((cup,))),
        (2, ObjectAtLoc((cup, setting_location)))],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive = False
    )

bowl = ptp.Variable('bowl')
setting_location = ptp.Variable('setting_location')
SetBowl = ptp.Operator(
    'SetBowl',
    target = BowlIsSet((bowl, setting_location)),
    suggesters = {},                         
    preconditions = [
        (1, LocKnown((bowl,))),
        (2, ObjectAtLoc((bowl, setting_location)))],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive = False
    )

obj = ptp.Variable('object')
location = ptp.Variable('location')
Put = ptp.Operator(
    'Put',
    target = ObjectAtLoc((obj, location)),
    suggesters = {},
    preconditions = [
        (1, ObjectInGripper((obj,)))],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive=True
    )

obj = ptp.Variable('object')
Pick = ptp.Operator(
    'Pick',
    target = ObjectInGripper((obj,)),
    suggesters = {},
    preconditions = [],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive=True
    )

obj = ptp.Variable('object')
DoDetection = ptp.Operator(
    'DoDetection',
    target = LocKnown((obj,)),
    suggesters = {},
    preconditions = [],
    side_effects = ptp.ConjunctionOfFluents([]),
    primitive=True
    )

operators = [SetTable, SetCup, SetBowl, Put, Pick, DoDetection]

if __name__ == '__main__':
    start_state = ptp.ConjunctionOfFluents([])
    world = SushiWorld(start_state)
    goal = ptp.ConjunctionOfFluents([TableIsSet((ptp.Symbol('table'),))])

    # run HPN to generate plan
    tree = ptp.HPlanTree()
    ptp.hpn(operators, start_state, goal, world, tree=tree)

    # write out a dot graph of the plan
    if len(sys.argv) > 1:
        outfile = sys.argv[1]
        f = open(outfile, 'w+')
        f.write(ptp.dot_from_plan_tree(tree).string())
        f.close()
        

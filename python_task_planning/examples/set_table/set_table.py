import roslib; roslib.load_manifest('hierarchical_interactive_planning')
import sys

import hierarchical_interactive_planning as hip

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
        self.current_state = hip.ConjunctionOfFluents(fluents)
        
        return self.current_state

    def entails(self, cof):
        return self.current_state.entails(cof)

######################################################################################################################
# Suggesters
######################################################################################################################

def table_to_set_suggester(current_state, goal):
    for f in goal.fluents:
        if f.name == 'TableIsSet':
            yield f._args[0]

def cup_suggester(current_state, goal):
    yield 'cup1'

def bowl_suggester(current_state, goal):
    yield bowl

def setting_location_suggester(current_state, goal):
    yield 'loc1'
    
######################################################################################################################
# Predicates
######################################################################################################################

TableIsSet = hip.Predicate('TableIsSet', ['table'])
CupIsSet = hip.Predicate('CupIsSet', ['cup'])
BowlIsSet = hip.Predicate('BowlIsSet', ['bowl'])
LocKnown = hip.Predicate('LocKnown', ['object'])
ObjectAtLoc = hip.Predicate('ObjectAtLoc', ['object', 'loc'])
ObjectInGripper = hip.Predicate('ObjectInGripper', ['object'])

######################################################################################################################
# Operators
######################################################################################################################

operators = [
    hip.Operator(
        'SetTable',
        target = TableIsSet(('Table',)),
        exists = {'Cup':cup_suggester, 'Bowl':bowl_suggester, 'SettingLocation':setting_location_suggester},
        preconditions = [
            (1, CupIsSet(('Cup', 'SettingLocation'))),
            (1, BowlIsSet(('Bowl', 'SettingLocation')))],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive = False
        ),

    hip.Operator(
        'SetCup',
        target = CupIsSet(('Cup', 'SettingLocation')),
        exists = {},
        preconditions = [
            (1, LocKnown(('Cup',))),
            (2, ObjectAtLoc(('Cup', 'SettingLocation')))],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive = False
        ),

    hip.Operator(
        'SetBowl',
        target = BowlIsSet(('Bowl', 'SettingLocation')),
        exists = {},                         
        preconditions = [
            (1, LocKnown(('Bowl',))),
            (2, ObjectAtLoc(('Bowl', 'SettingLocation')))],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive = False
        ),

    hip.Operator(
        'Put',
        target = ObjectAtLoc(('Object', 'Location')),
        exists = {},
        preconditions = [
            (1, ObjectInGripper(('Object',)))],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive=True
        ),

    hip.Operator(
        'Pick',
        target = ObjectInGripper(('Object',)),
        exists = {},
        preconditions = [],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive=True
        ),

    hip.Operator(
        'DoDetection',
        target = LocKnown(('Object',)),
        exists = {},
        preconditions = [],
        side_effects = hip.ConjunctionOfFluents([]),
        primitive=True
        )
    ]


if __name__ == '__main__':
    start_state = hip.ConjunctionOfFluents([])
    world = SushiWorld(start_state)
    goal = hip.ConjunctionOfFluents([TableIsSet(('table',))])

    # run HPN to generate plan
    tree = hip.HPlanTree()
    hip.hpn(operators, start_state, goal, world, tree=tree)

    # write out a dot graph of the plan
    if len(sys.argv) > 1:
        outfile = sys.argv[1]
        f = open(outfile, 'w+')
        f.write(hip.dot_from_plan_tree(tree).string())
        f.close()
        

import numpy as np
from hierarchical_interactive_planning import AbstractionInfo, ConjunctionOfFluents, HPlanTree
from hierarchical_interactive_planning.exceptions import PlanningFailedError
from hierarchical_interactive_planning.a_star import a_star

def hpn(operators, current_state, goal, world, abs_info=None, maxdepth=np.inf, depth=0, tree=None):
    '''Implements HPN (Hierarchical Planning in the Now) algorithm of Kaelbing and Lozano-Perez.

    Args:
        operators (list of Operator): Operators to use in the planning.
        current_state (ConjunctionOfFluents): Current state, represeneted as a conjunction of fluents.
        goal (ConjunctionOfFluents): Goal state, described as conjunction of fluents.
        world: Defined by the domain; used to execute operator instances and get the new state of the world.
        abs_info: (AbstractionInfo): Keeps track of abstraction level of the operators. Typically not passed in
            at the top level call.
        maxdepth (int): Max allowed depth of the planning hierarchy.
        depth (int): Current depth of the planning hierarchy.
        tree (HPlanTree): Data structure representing the hierarchical planning tree. Updated as this
            function recurses, and can be used to visualize the resulting plan.
    '''
    if depth > maxdepth:
        raise RuntimeError('Max recursion depth exceeded')

    if abs_info is None:
        abs_info = AbstractionInfo()

    plan = a_star(
        goal, # start from the goal and work backwards
        lambda s: world.entails(s), # we are done when we reach the current state
        lambda s: applicable_ops(operators, world, current_state, s, abs_info), # actions
        lambda s: num_violated_fluents(world, s) # heuristic
        )
    if plan is None:
        raise PlanningFailedError('A* could not find a plan')
    plan.reverse()

    tree.plan = []
    for op, subgoal in plan:
        tree.plan.append((op, HPlanTree(subgoal)))

    for op, subtree in tree.plan:
        subgoal = subtree.goal

        if op is None:
            pass
        elif op.concrete:
            print 'Executing:', op
            current_state = world.execute(op)
        else:
            abs_info.inc_abs_level(op.target)
            hpn(operators, current_state, subgoal, world, abs_info.copy(), maxdepth, depth+1, subtree)

def plan_flat(operators, world, current_state, goal):
    '''Uses goal regression to plan without any hierarchy. Useful for testing.
    '''
    class ConcreteAbs:
        def get_abs_level(self, f):
            return np.inf

    class ZeroAbs:
        def get_abs_level(self, f):
            return 0
        
    plan = a_star(
        goal, # start from the goal and work backwards
        lambda s: current_state.entails(s), # we are done when we a state that is already true
        lambda s: applicable_ops(operators, world, current_state, s, ConcreteAbs()), # actions
        lambda s: num_violated_fluents(current_state, s) # heuristic
        )
    if plan == None:
        return None
    return list(reversed(plan))
    
def applicable_ops(operators, world, current_state, goal, abs_info):
    for op in operators:
        for op_inst in op.gen_instances(world, current_state, goal, abs_info):
            subgoal = regress(goal, op_inst)
            if subgoal:
                yield op_inst, subgoal, 1 # cost fixed to 1 for all ops right now

def num_violated_fluents(world, subgoal):
    '''Computes the "distance" between a conjunction of fluents and
    the start conjunction of fluents.
    '''
    return sum([(not world.entails(f)) for f in subgoal.fluents])
            
def regress(g, o):
    '''Constructs the weakest preimage state from which the given operator
    would achieve all of the fluents in the given state.

    Returns:
        g_pre (ConjunctionOfFluents or None): Weakest preimage, or None if no preimage exists.
    '''
    if o.target.contradicts(g) or o.side_effects.contradicts(g):
        return None
 
    g_pre = []
    for f_g in g.fluents:
        if not (o.target.entails(f_g) or o.side_effects.entails(f_g)):
            g_pre.append(f_g)

    for f in o.preconditions.fluents:
        if f not in g_pre:
            g_pre.append(f)
        
    return ConjunctionOfFluents(g_pre)

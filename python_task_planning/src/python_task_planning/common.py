class Symbol:
    def __init__(self, val=None):
        self.val = val

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return (self is other)

    def __repr__(self):
        return 'symbol%d' % id(self)

class Variable:
    def __init__(self, name):
        self.name = name

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return (self is other)

    def __repr__(self):
        return str(self.name)

class Fluent:
    def __init__(self, pred, args):
        self.pred = pred
        self.args = tuple(args)

    def __hash__(self):
        '''Hash depends only on the fluent class and args.
        '''
        return hash((self.pred, self.args))

    def __eq__(self, other):
        '''Equality depends only on fluent class and args.
        '''
        return (self.pred, self.args) == (other.pred, other.args)

    def __repr__(self):
        return '%s(%s)' % (self.pred.name, ', '.join([str(a) for a in self.args]))

    def match(self, other):
        '''Returns a dictionary of bindings which map variables in this fluent
        to variables/values in another fluent.
        '''
        if not other.pred == self.pred:
            return None

        bindings = {}
        for arg_self, arg_other in zip(self.args, other.args):
            # (strings starting with upper case are assumed to be variables)
            if (not isinstance(arg_other, Variable)):
                if isinstance(arg_self, Variable):
                    print 'binding:', arg_self, arg_other
                    bindings[arg_self] = arg_other
                else:
                    print 'not binding:', arg_self, arg_other
                    if not arg_self == arg_other:
                        return None
            else:
                # for now assuming we always bind every variable. should
                # relax this in the future.
                raise ValueError('All variables must get bound!')
        return bindings

    def bind(self, bindings):
        '''Returns a copy of itself with the given bindings applied.
        '''
        return Fluent(self.pred, [bindings.get(arg, arg) for arg in self.args])
                
    def entails(self, other):
        return self == other

    def contradicts(self, other):
        return False

class Predicate:
    def __init__(self, name, argnames):
        self.name = name
        self.argnames = argnames

    def __call__(self, args):
        return Fluent(self, args)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

class ConjunctionOfFluents:
    def __init__(self, fluents):
        '''State represented as a conjunction of fluents.
        '''
        self.fluents = tuple(fluents)

    def __hash__(self):
        '''Using sum because hash should be the same regardless of the
        order of the fluents.
        '''
        return hash(sum([hash(f) for f in self.fluents]))

    def __repr__(self):
        if len(self.fluents) > 0:
            return ' ^ '.join([str(f) for f in self.fluents])
        else:
            return '---'

    def _entails_fluent(self, f):
        return any([fs.entails(f) for fs in self.fluents])
    
    def _contradicts_fluent(self, f):
        return any([fs.contradicts(f) for fs in self.fluents])

    def bind(self, bindings):
        '''Return a copy of itself with the given bindings applied.
        '''
        return ConjunctionOfFluents([f.bind(bindings) for f in self.fluents])

    def entails(self, other):
        if isinstance(other, Fluent):
            return self._entails_fluent(other)
        elif isinstance(other, ConjunctionOfFluents):
            return all([self._entails_fluent(f) for f in other.fluents])
        else:
            TypeError('Cannot operate on %s' % str(other))

    def contradicts(self, other):
        if isinstance(other, Fluent):
            return self._contradicts_fluent(other)
        elif isinstance(other, ConjunctionOfFluents):
            return any([self._contradicts_fluent(f) for f in other.fluents])
        else:
            TypeError('Cannot operate on %s' % str(other))

class AbstractionInfo:
    def __init__(self, fluent_counts={}):
        self.fluent_counts = fluent_counts

    def __repr__(self):
        return 'AbstractionInfo(%s)' % repr(self.fluent_counts)

    def inc_abs_level(self, f):
        if not f in self.fluent_counts:
            self.fluent_counts[f] = 0
        self.fluent_counts[f] += 1

    def get_abs_level(self, f):
        if not f in self.fluent_counts:
            return 0
        else:
            return self.fluent_counts[f]

    def copy(self):
        return AbstractionInfo(self.fluent_counts.copy())

class Operator:
    def __init__(self, name, target, suggesters, preconditions, side_effects, primitive):
        self.name = name
        self.target = target
        self.suggesters = suggesters
        self.preconditions = preconditions
        self.side_effects = side_effects
        self.primitive = primitive

    def __repr__(self):
        return '%s()' % self.name

    def gen_instances(self, world, current_state, goal, abs_info):
        for goal_fluent in goal.fluents:
            bindings = self.target.match(goal_fluent)
            if bindings == None:
                continue

            # bind target and calculate current abstraction level
            target = self.target.bind(bindings)
            abs_level = abs_info.get_abs_level(target)

            for other_bindings in suggest_values(self.suggesters, world, current_state, goal):
                bindings.update(other_bindings)

                pc_fluents = []
                for abs_n, f in self.preconditions:
                    if abs_n <= abs_level:
                        pc_fluents.append(f.bind(bindings))
                preconditions = ConjunctionOfFluents(pc_fluents)
                side_effects = self.side_effects.bind(bindings)
                concrete = (len(preconditions.fluents) == len(self.preconditions))

                yield OperatorInstance(self.name, abs_level,
                    target, preconditions, side_effects, self.primitive, concrete)

class OperatorInstance:
    def __init__(self, operator_name, abs_level, target, preconditions, side_effects, primitive, concrete):
        self.operator_name = operator_name
        self.abs_level = abs_level
        self.target = target
        self.preconditions = preconditions
        self.side_effects = side_effects
        self.primitive = primitive
        self.concrete = concrete

    def __repr__(self):
        return 'A%d: %s(%s)' % (self.abs_level, self.operator_name, ', '.join([str(a) for a in self.target.args]))

class HPlanTree:
    def __init__(self, goal=None, plan=None):
        self.goal = goal
        self.plan = plan

    def __str__(self):
        if self.plan == None:
            return str(self.goal)
        else:
            return '%s( %s )' % (self.goal, ' '.join([str(st) for (op, st) in self.plan]))
    

def suggest_values(vars, world, current_state, goal):
    '''Suggest values for all variables in the given dictionary.
    
    Args:
        vars (dict): Dictionary in which the keys are variables, and the values are
            suggesters for that variable.
        current_state (State): Current world state.
        goal (ConjunctionOfFluents): Goal conjunction.
    '''
    if len(vars) == 0:
        yield {}
        return

    remaining_vars = vars.copy()
    varname, suggester = remaining_vars.popitem()
    for val in suggester(world, current_state, goal):
        if len(remaining_vars) == 0:
            yield {varname: val}
        else:
            for values in suggest_values(remaining_vars, world, current_state, goal):
                values[varname] = val
                yield values

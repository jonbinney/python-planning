class ConjunctionOFluents:
    def __init__(self, fluents):
        self.fluents = fluents

class Fluent(ConjunctionOfFluents):
    def __init__(self, pred, argnames, args):
        self.pred = pred
        self.argnames = argnames
        self.args = args
        self.rval = rval

    def __and__(self, other):


class Predicate:
    def __init__(self, name, argnames):
        self.name = name
        self.argnames = argnames

    def __call__(self, args):
        return Fluent(self.name, self.argnames, args)

def TableIsSet(table):
    return Fluent('TableIsSet', ['table'], [table])


class Conjunction(Predicate):
    def __init__(self, args
    
                    

TableIsSet = Predicate('TableIsSet', argnames=['Table'])

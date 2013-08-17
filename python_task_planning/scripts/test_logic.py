import roslib; roslib.load_manifest('hip')
from hip import Fluent, ConjunctionOfFluents

f1 = Fluent('On', ('bowl', 'table'), 'true')
f2 = Fluent('Holding', ('right_gripper',), 'nothing')
f3 = Fluent('Holding', ('right_gripper',), 'bowl')

# fluents with variables
f4 = Fluent('On', ('Object1', 'Object2'), 'Bool1')
f5 = Fluent('Holding', ('Gripper',), 'Object1')

target = f4
side_effects = ConjunctionOfFluents((f4, f5))

bindings = target.match(f1)
print bindings
print side_effects.bind(bindings)

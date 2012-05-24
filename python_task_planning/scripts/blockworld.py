import numpy as np
from scipy import linalg

# State

class BlockState(hip.State):
    def __init__(self, grid, robot_start_pos):
        self.grid = np.array(grid)
        self.robot_pos = robot_start_pos
        hip.

# Suggesters

class SuggestPosition(hip.Suggester):
    def __init__(self):
        hip.Suggester.__init__(self)

    def suggest(self, start, goal, bindings):
        

# Operators

class Move(hip.Primitive):
    def __init__(self, step):
        self.step = np.array(step)
        exists = {'p':SuggestPositions()}
        preconditions = [AtPosition(p), IsValidMove(self, p)]
        target = AtPosition(p + step)
        side_effects = set()
        cost = linalg.norm(self.step)
        hip.State.__init__(self, preconditions, target, side_effects, cost)

    def preconditions(self, s):

    def execute(self, s):
        s.robot_pos += self.direction

# Fluents

class CurrentPosition:
    def __init__(self):
        hip.Fluent.__init__(self)

    def evaluate(self, s):
        return s.robot_pos

class IsValidMove(hip.Fluent):
    def __init__(self, move):
        self.move = move
        hip.Fluent.__init__(self)

    def evaluate(self, s):
        x, y = s.robot_pos + self.move.step
        if x >= 0 and x < s.grid.shape[0] and y >= 0 and y < s.grid.shape[1]:
            return True
        else:
            return False

class AtPosition(hip.Fluent):
    def __init__(self, target_position):
        self.target_position = np.array(target_position)
        hip.Fluent.__init__(self)

    def evaluate(self, s):
        if s.robot_pos == self.target_position:
            return True
        else:
            return False

# Problem

class BlockProblem(hip.Problem):
    def __init__(self):
        self.operators = [Move((0, -1)), Move((0, 1)), Move((1, 0)), Move((-1, 0))]
    

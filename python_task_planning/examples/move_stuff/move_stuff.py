'''
Example which moves objects around in a 2D world.

This example requires matplotlib. The ros package doesnt have this as a
rosdep though, since nothing else needs it. Just do a system install
of matplotlib.
'''
import roslib; roslib.load_manifest('hierarchical_interactive_planning')
import numpy as np
from scipy import linalg

import hierarchical_interactive_planning as hip

######################################################################################################################
# World
######################################################################################################################

class MoveStuffWorld:
    def __init__(self, obs_map, objects, eps=1.0):
        '''
        Args:
            objects (dict): Mapping from string object names to numpy arrays of their positions.
        '''
        self.obs_map = obs_map
        self.objects = objects
        self.eps = eps

    def execute(self, op_instance):
        op_name = op_instance.operator_name
        if op_name == 'MoveTo':
            x_des = op_instance.target.args[0].val
            self.objects['robot'].position = x_des
        else:
            raise ValueError('Unknown operator: %s' % str(operator.name))            

    def entails(self, f):
        if isinstance(f, hip.ConjunctionOfFluents):
            return np.all([self.entails(fluent) for fluent in f.fluents])
        
        if f.pred == RobotAtLoc:
            x_robot = self.objects['robot'].position
            x_des = f.args[0].val
            if linalg.norm(x_robot - x_des) < self.eps:
                return True
            else:
                return False
        else:
            raise ValueError('Unknown predicate: %s' % str(f.pred))

    def contradicts(self, f):
        return False

    def plan_path(self, x_start, x_end, n_graph_points=1000, graph_conn_dist=1.0):
        '''Plan a collision free path from x_start to x_end.

        Returns:
            path (list of np.array): Path (or None if no path found).
        '''
        # build a random graph
        x_min, x_max, y_min, y_max = self.obs_map.extent()
        points = np.zeros((n_graph_points, 2))
        points[:,0] = np.random.uniform(x_min, x_max, n_graph_points)
        points[:,1] = np.random.uniform(y_min, y_max, n_graph_points)
        
        def action_generator(state):
            for neighbor in range(len(points)):
                d = linalg.norm(points[state] - points[neighbor])
                if d < conn_dist:
                    yield neighbor, neighbor, d  # action, next_state, cost

        p = a_star.a_star(
            start,
            lambda s: s == goal,
            action_generator,
            lambda s: linalg.norm(points[goal] - points[s])
            )
        


class Robot:
    def __init__(self, position):
        self.position = position

class Box:
    def __init__(self, center, r):
        self.center = np.array(center)
        self.r = r

######################################################################################################################
# Predicates
######################################################################################################################

RobotAtLoc = hip.Predicate('RobotAtLoc', ['loc'])
RobotLocFree = hip.Predicate('RobotLocFree', ['robot', 'loc'])

######################################################################################################################
# Suggesters
######################################################################################################################

def robot_path_suggester(world, current_state, goal):
    for f in goal.fluents:
        if f.pred == RobotAtLoc:
            x_des = f.args[0].val
    yield []

######################################################################################################################
# Operators
######################################################################################################################

loc = hip.Variable('loc')
path = hip.Variable('path')
MoveTo = hip.Operator(
    'MoveTo',
    target = RobotAtLoc((loc,)),
    suggesters = {path:robot_path_suggester},
    preconditions = [],
    side_effects = hip.ConjunctionOfFluents([]),
    primitive = False,
    )

operators = [MoveTo]

######################################################################################################################
# Main
######################################################################################################################

def draw_objects(objects):
    for obj_name, obj in objects.items():
        if isinstance(obj, Box):
            plt.plot([obj.center[0]], [obj.center[1]], 'x')
            vertices = []
            r = obj.r
            for offset in [(r, r), (r, -r), (-r, -r), (-r, r)]:
                vertices.append(obj.center + np.array(offset))
            vertices = np.array(vertices)
            plt.fill(vertices[:,0], vertices[:,1], 'm')
        elif isinstance(obj, Robot):
            plt.plot([obj.position[0]], [obj.position[1]], 'go', markersize=40)

class ObstacleMap:
    def __init__(self, obs_array, res):
        '''2D obstacle map class.

        Args:
            obs_array (np.array of np.bool): Occupancy array.
            res (float): Size (height and width) of each cell in the occupancy array.
        '''
        self.obs_array = obs_array
        self.res = res

    def pos_to_ind(self, p):
        '''Return array index for cell that contains x,y position.
        '''
        ii, jj = np.array(p) / self.res
        return int(ii), int(jj)
    
    def ind_to_pos(self, ind):
        '''Return x,y position of center point of cell specified by index.
        '''
        return  np.array(ind) * self.res + 0.5 * self.res

    def is_occupied(self, p):
        ii, jj = self.pos_to_ind(p)
        return self.obs_array[ii,jj]

    def any_occupied(self, x0, x1, y0, y1):
        '''Return true if any cells within the bounding box are occupied.
        '''
        i0, j0 = self.pos_to_ind((x0, y0))
        i1, j1 = self.pos_to_ind((x1, y1))
        i0 = max(0, i0)
        i1 = max(0, i1)
        j0 = max(0, j0)
        j1 = max(0, j1)
        return self.obs_array[i0:i1,j0:j1].any()

    def points(self):
        points = []
        for ii in range(self.obs_array.shape[0]):
            for jj in range(self.obs_array.shape[1]):
                p = self.ind_to_pos((ii, jj))
                points.append(p)
        return np.array(points)

    def occupied_points(self):
        points = []
        for ii in range(self.obs_array.shape[0]):
            for jj in range(self.obs_array.shape[1]):
                p = self.ind_to_pos((ii, jj))                
                if self.is_occupied(p):
                    points.append(p)
        return np.array(points)

    def extent(self):
        x_min, y_min = self.ind_to_pos((0, 0))
        s = self.obs_array.shape
        x_max, y_max = self.ind_to_pos((s[0]-1, s[1]-1))
        return x_min, y_min, x_max, y_max

if __name__ == '__main__':
    import sys
    from matplotlib import pyplot as plt

    # load world map
    res = 1.0
    obs_arr = plt.imread(sys.argv[1])[::-1,:].T
    obs_arr = obs_arr < obs_arr.max() / 2.0
    obs_map = ObstacleMap(obs_arr, res)
    
    objects = {
        'robot': Robot(np.array((50., 50.))),
        'box1': Box((5., 5.), 4.),
        }

    start_state = hip.ConjunctionOfFluents([])
    world = MoveStuffWorld(obs_map, objects)
    goal_symbol = hip.Symbol(np.array((10., 10.)))
    goal = hip.ConjunctionOfFluents([RobotAtLoc((goal_symbol,))])

    # run HPN to generate plan
    tree = hip.HPlanTree()
    hip.hpn(operators, start_state, goal, world, tree=tree)
    
    
    fig = plt.figure()
    points_occ = obs_map.occupied_points()
    plt.plot(points_occ[:,0], points_occ[:,-1], 'bo')

    if 0:
        w = 5
        occ = []
        free = []
        for x, y in obs_map.points():
            if obs_map.any_occupied(x-w, x+w, y-w, y+w):
                occ.append((x, y))
            else:
                free.append((x, y))
        occ = np.array(occ)
        free = np.array(free)
        plt.plot(occ[:,0], occ[:,1], 'r.')            
        plt.plot(free[:,0], free[:,1], 'g.')
    
    draw_objects(objects)
    x_min, x_max, y_min, y_max = obs_map.extent()
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.show()



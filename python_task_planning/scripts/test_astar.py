#!/usr/bin/env python
from python_task_planning import a_star

import numpy as np
from scipy import linalg
from matplotlib import pyplot as plt

n = 1000
conn_dist = 0.1

points = np.random.random((n, 2))

def action_generator(state):
    for neighbor in range(len(points)):
        d = linalg.norm(points[state] - points[neighbor])
        if d < conn_dist:
            yield neighbor, neighbor, d  # action, next_state, cost
        
start = 0
goal = n-1
p = a_star.a_star(
    start,
    lambda s: s == goal,
    action_generator,
    lambda s: linalg.norm(points[goal] - points[s])
    )
print p

plt.plot(points[:,0], points[:,1], 'b.')
plt.plot([points[start][0]], [points[start][1]], 'ro')
plt.plot([points[goal][0]], [points[goal][1]], 'go')

path_points = np.array([points[ii] for (ii, ii) in p])
plt.plot(path_points[:,0], path_points[:,1], 'm-o')

plt.show()

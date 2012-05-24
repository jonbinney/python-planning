def a_star(start, goal_test, action_generator, heuristic):
    '''
    Taken almost verbatim from http://en.wikipedia.org/wiki/A*_search_algorithm.

    Args:
        start: Start state.
        goal_test: Function which takes a state and returns True iff it is a goal state.
        action_generator: Generator which takes a state and yields all possible pairs (action, next_state state)
            of actions a that can be taken, and the next state which they will yield.
        heuristic: Function which takes a state and returns its heuristic value.
    '''
    closed_set = set()
    open_set = set([start])
    came_from = {}
    action_used = {}

    g_score = {start: 0.0}
    h_score = {start: heuristic(start)}
    f_score = {start: g_score[start] + h_score[start]}

    while len(open_set) > 0:
        current = min(open_set, key=f_score.get)
        if goal_test(current):
            path = reconstruct_path(came_from, action_used, current)
            actions = reconstruct_actions(path, action_used)
            return zip(actions, path)

        open_set.remove(current)
        closed_set.add(current)
        for action, neighbor, cost in action_generator(current):
            if neighbor in closed_set:
                continue
            tentative_g_score = g_score[current] + cost

            if neighbor not in open_set:
                open_set.add(neighbor)
                h_score[neighbor] = heuristic(neighbor)
                tentative_is_better = True
            elif tentative_g_score < g_score[neighbor]:
                tentative_is_better = True
            else:
                tentative_is_better = False

            if tentative_is_better:
                came_from[neighbor] = current
                action_used[neighbor] = action
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + h_score[neighbor]
    return None
            
def reconstruct_path(came_from, action_used, current_state):
    if current_state in came_from:
        p = reconstruct_path(came_from, action_used, came_from[current_state])
        return p + [current_state]
    else:
        return [current_state]

def reconstruct_actions(path, action_used):
    actions = []
    for ii in range(len(path)):
        if ii + 1 < len(path):
            next_state = path[ii+1]
            actions.append(action_used[next_state])
        else:
            actions.append(None)
    return actions

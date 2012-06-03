from python_task_planning import ConjunctionOfFluents, OperatorInstance
import pygraphviz as pgv

lpk_style = dict(
    operator_instance = dict(shape='box', style='filled', color='thistle1'),
    primitive = dict(shape='box', style='filled', color='darkseagreen1'),
    plan_goal = dict(shape='box', style='filled', color='lightsteelblue1'),
    plan_step_arrow = dict(),
    refinement_arrow = dict(style='dashed')
)

garish_style = dict(
    operator_instance = dict(shape='box', style='filled', color='red'),
    primitive = dict(shape='box', style='filled', color='green'),
    plan_goal = dict(shape='box', style='filled', color='blue'),
    plan_step_arrow = dict(),
    refinement_arrow = dict(style='dashed')
)



def dot_from_plan_tree(tree, G=None, style=None):
    if G is None:
        G = pgv.AGraph(strict=True, directed=True)

    if style is None:
        style = lpk_style

    G.add_node(id(tree), label=str(tree.goal), **style['plan_goal'])
    if not tree.plan == None:
        for op, subtree in tree.plan:
            if op == None:
                pass
            elif op.concrete:
                G.add_node(id(op), label=str(op), **style['primitive'])
                G.add_edge(id(tree), id(op), **style['plan_step_arrow'])                
            else:
                G.add_node(id(op), label=str(op), **style['operator_instance'])
                G.add_edge(id(tree), id(op), **style['plan_step_arrow'])
                dot_from_plan_tree(subtree, G, style)
                G.add_edge(id(op), id(subtree), **style['refinement_arrow'])
    return G

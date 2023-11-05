import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime as dt
import networkx as nx
import numpy as np
import time
import itertools as ittls

# log is 2d list, each element is trace with activities
# log1 = [['a','b','c','d']]*3 + [['a','c','b','d']]*2 + [['a','e','d']]
log1 = [['a','b','d'],
        ['a','b','c','b','d'],
        ['a','b','c','b','c','b','d'],]

def get_all_act(input_log):
    act_set = set()
    for trace in input_log:
        for act in trace:
            act_set.add(act)
    
    return act_set

def get_all_direct_succession(input_log):
    direct_succ_set = set()
    for trace in input_log:
        for i in range(0, len(trace) - 1):
            direct_succ_set.add((trace[i], trace[i + 1]))
    
    return direct_succ_set

def get_all_length_two_loop(input_log):
    length_two_set = set()
    for trace in input_log:
        for i in range(0, len(trace) - 2):
            if trace[i] == trace[i + 2] and trace[i] != trace[i + 1]:
                length_two_set.add((trace[i], trace[i + 1],trace[i + 2]))
    
    return length_two_set


def get_all_diamond(input_log):
    # (a,b,a) , (b,a,b) 를 만족하는 관계  => a diamond b
    length_two_set = get_all_length_two_loop(input_log)
    diamond_set = set()
    for e1,e2,e3 in length_two_set:
        if (e2,e1,e2) in length_two_set:
            diamond_set.add((e1, e2))

    return diamond_set

def get_footprint_matrix(input_log):
    all_act = sorted(list(get_all_act(input_log)))
    all_direct_succ = sorted(list(get_all_direct_succession(input_log)))
    all_diamond = list(get_all_diamond(input_log))

    footprint_matrix = { key1:{} for key1 in all_act}

    for a in all_act:
        for b in all_act:
            if (a, b) in all_direct_succ and (b,a) in all_direct_succ and (a,b) not in all_diamond:
                footprint_matrix[a][b] = '||' # parallel
            elif (a, b) in all_direct_succ and ((b, a) not in all_direct_succ or (a, b) in all_diamond):
                footprint_matrix[a][b] = '->'
            elif (b, a) in all_direct_succ and (a, b) not in all_direct_succ:
                footprint_matrix[a][b] = '<-'
            else:
                footprint_matrix[a][b] = '#'
    print(all_diamond, 'dia')
    return footprint_matrix

def get_first_task(input_log):
    task_set = set()
    for trace in input_log:
        task_set.add(trace[0])
    
    return task_set

def get_last_task(input_log):
    task_set = set()
    for trace in input_log:
        task_set.add(trace[len(trace) - 1])
    
    return task_set

def is_choice(a,b,footprint_matrix):
    if footprint_matrix[a][b] == '#':
        return True
    
    return False

def is_choice_set(act_lst, footprint_matrix):
    # check if all elements of list have choice relation
    combinations = []
    combinations += ittls.combinations(act_lst, 2)

    for a, b in combinations:
        if not is_choice(a, b, footprint_matrix):
            return False

    return True

def get_causality_set(act, footprint_matrix, is_row = True):
    # get list or set of B such that act -> b, b is in B
    causality_set = []
    for key in list(footprint_matrix[act].keys()):
        if is_row:
            if footprint_matrix[act][key] == '->':
                causality_set.append(key)
        else:
            if footprint_matrix[key][act] == '->':
                causality_set.append(key)

    return causality_set

def get_X_L(input_log):
    T_L = sorted(list(get_all_act(input_log)))
    T_I, T_O = list(get_first_task(input_log)), list(get_last_task(input_log))

    X_L = set()
    for act in T_L:
        causality_lst = get_causality_set(act, footprint_matrix, is_row = True)
        subsets = []
        for i in range(1, len(causality_lst) + 1):
            subsets += ittls.combinations(causality_lst, i)
        
        for subset in subsets:
            if len(subset) < 2:
                X_L.add((act,subset[0]))
                continue
            if is_choice_set(subset, footprint_matrix):
                X_L.add((act,subset))
        
        causality_lst = get_causality_set(act, footprint_matrix, is_row = False)
        subsets = []
        for i in range(1, len(causality_lst) + 1):
            subsets += ittls.combinations(causality_lst, i)
        
        for subset in subsets:
            if len(subset) < 2:
                X_L.add((subset[0],act))
                continue
            if is_choice_set(subset, footprint_matrix):
                X_L.add((subset,act))
    
    print("X_L: ",X_L)
    return X_L

def is_subset(element1, element2):
    # check if element1 in X_L is subset of element2
    is_sub1 = set(element1[0]).issubset(set(element2[0]))
    is_sub2 = set(element1[1]).issubset(set(element2[1]))

    return is_sub1 and is_sub2

def get_Y_L(input_log):
    T_L = sorted(list(get_all_act(input_log)))
    T_I, T_O = list(get_first_task(input_log)), list(get_last_task(input_log))

    X_L = list(get_X_L(input_log))
    Y_L = X_L.copy()
    remove_set = set()
    for i in range(len(X_L)):
        for j in range(len(X_L)):
            if i == j:
                continue
            if is_subset(X_L[i], X_L[j]):
                remove_set.add(X_L[i])
                break
    
    for remove_element in remove_set:
        Y_L.remove(remove_element)

    print('Y_L: ',Y_L)
    return Y_L
                



footprint_matrix = get_footprint_matrix(log1)

print(pd.DataFrame(footprint_matrix).transpose())
# pandas는 [열][행] 으로 인덱싱 해야한다
# print(footprint_matrix['b']['a'])
# print(list(footprint_matrix['a'].keys()))




def draw_petrinet(input_log,Y_L):
    T_L = sorted(list(get_all_act(input_log)))
    T_I, T_O = list(get_first_task(input_log)), list(get_last_task(input_log))
    G = nx.DiGraph()

    # G.add_node('start')
    # for act in T_L:
    #     G.add_node(act)
    # for place in Y_L:
    #     G.add_node(place)
    # G.add_node('end')
    # 엣지 설정
    for act in T_I:
        G.add_edge('start', act)
    for place in Y_L:
        sources, targets = place
        for source in sources:
            G.add_edge(source, place)
        for target in targets:
            G.add_edge(place, target)
    for act in T_O:
        G.add_edge(act,'end')

    node_shapes = {act: 's' for act in T_L}
    
    pos = nx.spring_layout(G)
    # for node in G:
    #     nx.draw_networkx_nodes(G, pos, nodelist=[node], 
    #                             node_size=1500, 
    #                             node_color='skyblue' if node_shapes[node] == 'o' else 'lightgreen',
    #                             node_shape=node_shapes[node])
    nx.draw_networkx_nodes(G, pos=pos, nodelist=T_L, node_shape='s')
    nx.draw_networkx_nodes(G, pos=pos, nodelist=Y_L+['start','end'], node_shape='o')
    nx.draw_networkx_edges(G,pos=pos)
    nx.draw_networkx_labels(G,pos=pos,font_size=9)
    # nx.draw(G,with_labels=True,pos=pos)
    plt.show()

Y_L = get_Y_L(log1)
draw_petrinet(log1, Y_L)
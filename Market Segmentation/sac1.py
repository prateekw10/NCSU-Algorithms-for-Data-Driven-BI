import numpy as np
import pandas as pd
import igraph as ig
from sklearn.metrics.pairwise import cosine_similarity
import sys

def calculateModularityAttribute(g, cluster_i, cluster_j):
    cluster_i_attributes = []
    for node in cluster_i:
        cluster_i_attributes.append(list(g.vs[node].attributes().values()))
    cluster_i_centroid = [sum(x)/len(cluster_i) for x in zip(*cluster_i_attributes)]
    cluster_j_attributes = []
    for node in cluster_j:
        cluster_j_attributes.append(list(g.vs[node].attributes().values()))
    cluster_j_centroid = [sum(x)/len(cluster_j) for x in zip(*cluster_j_attributes)]
    similarity = cosine_similarity(np.array(cluster_i_centroid).reshape(1,-1), np.array(cluster_j_centroid).reshape(1,-1))[0][0]
    return similarity

if __name__ == "__main__":

    # Read graph attributes
    attributes = pd.read_csv("data/fb_caltech_small_attrlist.csv")

    # Read edge list
    edgeList = []
    with open("data/fb_caltech_small_edgelist.txt", "r") as text_file:
        for line in text_file:
            edge = line.strip().split(' ')
            edgeList.append([int(i) for i in edge])

    alpha = float(sys.argv[1])

    # Construct graph using igraph package
    max_users = 324
    g = ig.Graph()
    g.add_vertices(max_users)
    g.add_edges(edgeList)

    # Assign attribtues to graph vertices
    columns = attributes.columns
    for column in columns:
        g.vs[column] = attributes[column]

    # Implement SAC-1 Algorithm
    membership = list(range(0,max_users))
    extra_membership = dict()

    for k in range(15):
        if k > 0:
            g.contract_vertices(membership, combine_attrs=sum)
            g = g.simplify(combine_edges=sum, multiple=True, loops=False)
            if len(membership) > len(g.vs):
                for x, y in enumerate(membership[len(g.vs):]):
                    extra_membership[len(g.vs)+x] = y
            membership = membership[:len(g.vs)]

        vc = ig.clustering.VertexClustering(g, membership)
        changed_membership = membership.copy()
        for i,cluster_i in enumerate(vc.__iter__()):
            if len(cluster_i) > 0:
                vc = ig.clustering.VertexClustering(g,membership)
                initialModularity = vc.modularity
                cluster_max, modularity_max = [], 0
                for cluster_j in vc.__iter__():
                    if len(cluster_j) > 0 and cluster_i != cluster_j:
                        membership_temp = membership.copy()
                        for node in cluster_i:
                            membership_temp[node] = membership_temp[cluster_j[0]]
                        vc_temp = ig.clustering.VertexClustering(g,membership_temp)
                        delta_Newman = vc_temp.modularity - initialModularity
                        delta_Attribute = calculateModularityAttribute(g, cluster_i, cluster_j)
                        delta_modularity = alpha * delta_Newman + (1-alpha) * delta_Attribute
                        if modularity_max < delta_modularity:
                            cluster_max = cluster_j
                            modularity_max = delta_modularity
                if modularity_max > 0.01:
                    for node in cluster_i:
                        changed_membership[node] = changed_membership[cluster_max[0]]
        if(changed_membership == membership):
            break
        else:
            membership = changed_membership.copy()
            
    # Write output to file
    vc = ig.clustering.VertexClustering(g,membership)
    if alpha == 0.5:
        alpha = 5

    with open("communities_"+str(int(alpha))+".txt", 'w') as f:
        communities = list(vc.__iter__())
        for key, val in extra_membership.items():
            mem = [i for i, comm in enumerate(communities) if val in comm]
            communities[mem[0]].append(key)
        for cluster in communities:
            if len(cluster) > 0:
                f.write(",".join([str(x) for x in cluster]))
                f.write("\n")
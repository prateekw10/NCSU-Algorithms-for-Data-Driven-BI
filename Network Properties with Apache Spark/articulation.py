import sys
import time
import networkx as nx
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import functions
from graphframes import *
from copy import deepcopy

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

def checkArticulation(node, gNodes, gEdges, componentCount):
	gg = nx.Graph()
	#gg.add_nodes_from(gNodes.filter(lambda x: x != node).collect())
	#gg.add_edges_from(gEdges.filter(lambda (x,y): x != node and y != node).collect())
	newComponentCount = len(list(nx.connected_components(gg)))
	print(newComponentCount)
	return (node, newComponentCount == componentCount)

def articulations(g, usegraphframe=False):
	# Get the starting count of connected components
	componentCount = g.connectedComponents().select("component").distinct().count()
	gNodes = g.vertices.map(lambda x: x.id)
	gEdges = g.edges.map(lambda x: (x.src, x.dst))

	# Default version sparkifies the connected components process 
	# and serializes node iteration.
	if usegraphframe:
		# Get vertex list for serial iteration
        
		# For each vertex, generate a new graphframe missing that vertex
		# and calculate connected component count. Then append count to
		# the output
		for node in gNodes.collect():
			e = sqlContext.createDataFrame(gEdges.filter(lambda (x,y): x!=node and y!=node), ['src','dst'])
			v = sqlContext.createDataFrame(gNodes.filter(lambda x: x!=node).map(lambda x: (x, )), ['id'])
			gg = GraphFrame(v,e)
			componentCount2 = gg.connectedComponents().select("component").distinct().count()
			articulationDF = sqlContext.createDataFrame(gNodes.map(lambda x: (x, 1 if componentCount != componentCount2 else 0)),["id","articulation"])           

	# Non-default version sparkifies node iteration and uses networkx 
	# for connected components count.
	else:
		gg = nx.Graph()
		gg.add_nodes_from(gNodes.collect())
		gg.add_edges_from(gEdges.collect())
		points = list(nx.articulation_points(gg))
		articulationDF = sqlContext.createDataFrame(gNodes.map(lambda x: (x, 1 if x in points else 0)),["id","articulation"])

	return articulationDF

filename = sys.argv[1]
lines = sc.textFile(filename)

pairs = lines.map(lambda s: s.split(","))
e = sqlContext.createDataFrame(pairs,['src','dst'])
e = e.unionAll(e.selectExpr('src as dst','dst as src')).distinct() # Ensure undirectedness 	

# Extract all endpoints from input file and make a single column frame.
v = e.selectExpr('src as id').unionAll(e.selectExpr('dst as id')).distinct()	

# Create graphframe from the vertices and edges.
g = GraphFrame(v,e)

#Runtime approximately 5 minutes
print("---------------------------")
print("Processing graph using Spark iteration over nodes and serial (networkx) connectedness calculations")
init = time.time()
df = articulations(g, False)
print("Execution time: %s seconds" % (time.time() - init))
print("Articulation points:")
df.filter('articulation = 1').show(truncate=False)
df.toPandas().to_csv("articulation_out" + ".csv")
print("---------------------------")

#Runtime for below is more than 2 hours
print("Processing graph using serial iteration over nodes and GraphFrame connectedness calculations")
init = time.time()
df = articulations(g, True)
print("Execution time: %s seconds" % (time.time() - init))
print("Articulation points:")
df.filter('articulation = 1').show(truncate=False)

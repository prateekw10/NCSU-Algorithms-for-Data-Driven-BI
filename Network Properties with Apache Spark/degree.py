import sys
import pandas
import networkx as nx
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql.types import *
from graphframes import *

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

''' return the simple closure of the graph as a graphframe.'''
def simple(g):
	# Extract edges and make a data frame of "flipped" edges
	flippedEdges = sqlContext.createDataFrame(g.edges.map(lambda (x,y): (y,x)), ['src','dst'])

	# Combine old and new edges. Distinctify to eliminate multi-edges
	# Filter to eliminate self-loops.
	# A multigraph with loops will be closured to a simple graph
	# If we try to undirect an undirected graph, no harm done
	allEdges = g.edges.unionAll(flippedEdges)
	e = allEdges.filter(allEdges.src!=allEdges.dst).distinct()
    
	return GraphFrame(g.vertices,e)

''' Return a data frame of the degree distribution of each edge in
the provided graphframe '''
def degreedist(g):
	# Generate a DF with degree,count
    degreeList = g.inDegrees.groupBy("inDegree").count()
    degreeList.withColumnRenamed('degree','count')
    
    return degreeList

''' Read in an edgelist file with lines of the format id1<delim>id2
and return a corresponding graphframe. If "large" we assume
a header row and that delim = " ", otherwise no header and
delim = ","'''
def readFile(filename, large, sqlContext=sqlContext):
	lines = sc.textFile(filename)

	if large:
		delim=" "
		# Strip off header row.
		lines = lines.mapPartitionsWithIndex(lambda ind,it: iter(list(it)[1:]) if ind==0 else it)
	else:
		delim=","
   
	vschema = StructType([StructField("id", IntegerType())])
	eschema = StructType([StructField("src", IntegerType()),StructField("dst", IntegerType())])

	# Extract pairs from input file and convert to data frame matching
	# schema for graphframe edges.
	edges = lines.map(lambda x: x.split(delim))
	e = sqlContext.createDataFrame(edges, ['src','dst'])

	# Extract all endpoints from input file (hence flatmap) and create
	# data frame containing all those node names in schema matching
	# graphframe vertices
	vertices = lines.flatMap(lambda x: x.split(delim)).distinct().map(lambda x: (x, ))
	v = sqlContext.createDataFrame(vertices, ['id'])

	# Create graphframe g from the vertices and edges.
	g = GraphFrame(v,e)

	return g

def checkScaleFree(distrib, nodecount):
	for (x,y) in distrib.collect():
		if y/nodecount < x**(-3) or y/nodecount > x**(-2):
			return "Not Scale Free"
	return "Scale Free"
    
# main stuff

# If you got a file, yo, I'll parse it.
if len(sys.argv) > 1:
	filename = sys.argv[1]
	if len(sys.argv) > 2 and sys.argv[2]=='large':
		large=True
	else:
		large=False

	print("Processing input file " + filename)
	g = readFile(filename, large)

	print("Original graph has " + str(g.edges.count()) + " directed edges and " + str(g.vertices.count()) + " vertices.")

	g2 = simple(g)
	print("Simple graph has " + str(g2.edges.count()/2) + " undirected edges.")

	distrib = degreedist(g2)
	distrib.show()
	nodecount = g2.vertices.count()
	print("Graph has " + str(nodecount) + " vertices.")

	out = filename.split("/")[-1]
	print("Writing distribution to file " + out + ".csv")
	distrib.toPandas().to_csv(out + ".csv")


# Otherwise, generate some random graphs.
else:
	print("Generating random graphs.")
	vschema = StructType([StructField("id", IntegerType())])
	eschema = StructType([StructField("src", IntegerType()),StructField("dst", IntegerType())])

	gnp1 = nx.gnp_random_graph(100, 0.05, seed=1234)
	gnp2 = nx.gnp_random_graph(2000, 0.01, seed=5130303)
	gnm1 = nx.gnm_random_graph(100,1000, seed=27695)
	gnm2 = nx.gnm_random_graph(1000,100000, seed=9999)

	todo = {"gnp1": gnp1}#, "gnp2": gnp2, "gnm1": gnm1, "gnm2": gnm2}
	for gx in todo:
		print("Processing graph " + gx)
		vertices = sc.parallelize(todo[gx].nodes()).map(lambda x: (x, ))
		v = sqlContext.createDataFrame(vertices, ['id'])
		e = sqlContext.createDataFrame(sc.parallelize(todo[gx].edges()), ['src','dst'])
		g = simple(GraphFrame(v,e))
		distrib = degreedist(g)
		nodecount = g.vertices.count()
		print("Writing distribution to file " + gx + ".csv")
		distrib.toPandas().to_csv(gx + ".csv")
        
print(checkScaleFree(distrib, nodecount))

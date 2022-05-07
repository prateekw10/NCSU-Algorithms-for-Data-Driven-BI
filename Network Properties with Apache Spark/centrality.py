from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import functions
from graphframes import *
from pyspark.sql.functions import explode

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

def closeness(g):
	
	# Get list of vertices. We'll generate all the shortest paths at
	# once using this list.
	verticesList = g.vertices.rdd.flatMap(lambda x: x).collect()

	# first get all the path lengths.
	results = g.shortestPaths(landmarks=verticesList)

	# Break up the map and group by ID for summing
	paths = results.select(results.id,explode(results.distances))

	# Sum by ID
	groups = paths.groupBy("id").sum("value")

	# Get the inverses and generate desired dataframe.
	centralityDF = sqlContext.createDataFrame(groups.map(lambda (x, y): (x, 1/float(y))), ['id','closeness'])
    
	return centralityDF

print("Reading in graph for problem 2.")
graph = sc.parallelize([('A','B'),('A','C'),('A','D'),
	('B','A'),('B','C'),('B','D'),('B','E'),
	('C','A'),('C','B'),('C','D'),('C','F'),('C','H'),
	('D','A'),('D','B'),('D','C'),('D','E'),('D','F'),('D','G'),
	('E','B'),('E','D'),('E','F'),('E','G'),
	('F','C'),('F','D'),('F','E'),('F','G'),('F','H'),
	('G','D'),('G','E'),('G','F'),
	('H','C'),('H','F'),('H','I'),
	('I','H'),('I','J'),
	('J','I')])
	
e = sqlContext.createDataFrame(graph,['src','dst'])
v = e.selectExpr('src as id').unionAll(e.selectExpr('dst as id')).distinct()
print("Generating GraphFrame.")
g = GraphFrame(v,e)

print("Calculating closeness.")
closeness(g).sort('closeness',ascending=False).show()

print("Writing closeness to file centrality_out.csv")
closeness(g).sort('closeness',ascending=False).toPandas().to_csv("centrality_out" + ".csv")

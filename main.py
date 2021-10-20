from neo4j import GraphDatabase
from collections import defaultdict


def dijsktra(graph, initial, end):
    shortest_paths = {initial: (None, 0)}
    current_node = initial
    visited = set()

    while current_node != end:
        visited.add(current_node)
        destinations = graph.edges[current_node]
        weight_to_current_node = shortest_paths[current_node][1]

        for next_node in destinations:
            weight = graph.weights[(current_node, next_node)] + weight_to_current_node
            if next_node not in shortest_paths:
                shortest_paths[next_node] = (current_node, weight)
            else:
                current_shortest_weight = shortest_paths[next_node][1]
                if current_shortest_weight > weight:
                    shortest_paths[next_node] = (current_node, weight)

        next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
        if not next_destinations:
            return "Route Not Possible"
        current_node = min(next_destinations, key=lambda k: next_destinations[k][1])

    path = []
    while current_node is not None:
        path.append(current_node)
        next_node = shortest_paths[current_node][0]
        current_node = next_node
    #path = path[::-1]
    return path


class Graph:
    def __init__(self):
        self.edges = defaultdict(list)
        self.weights = {}

    def add_edge(self, from_node, to_node, weight):
        self.edges[from_node].append(to_node)
        self.edges[to_node].append(from_node)
        self.weights[(from_node, to_node)] = weight
        self.weights[(to_node, from_node)] = weight


class Neo4jWorkspace:
    DatabaseName = ""

    def __init__(self, uri, user, password, name):
        print("INFO: Setting URL for connection to BD . . .")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.DatabaseName = name

    def close(self):
        self.driver.close()
        print("INFO: BD closed")

    @staticmethod
    def _getLabel(tx, node):
        results = tx.run("MATCH (A) WHERE A.name='"+node+"' RETURN labels(A) as labels")
        return [r["labels"] for r in results]

    def returnLabel(self, node):
        with self.driver.session(database=self.DatabaseName) as session:
            label = session.read_transaction(self._getLabel, node)
            return label

    @staticmethod
    def _getLength(tx, start, end):
        query = "MATCH (A), (B) WHERE A.name='" + start + "' AND B.name='" + end + "' OPTIONAL MATCH (A)-[r]->(B) RETURN r.length as length"
        results = tx.run(query)
        return [r["length"] for r in results]

    def findRelation(self, start, end):
        with self.driver.session(database=self.DatabaseName) as session:
            length = session.read_transaction(self._getLength, start, end)
            return length

    @staticmethod
    def _getAllNodes(tx):
        results = tx.run("MATCH (A) RETURN A.name as name")
        return [r["name"] for r in results]

    def findAllNodes(self):
        print("INFO: Reading all nodes . . .")
        with self.driver.session(database=self.DatabaseName) as session:
            all_nodes = session.read_transaction(self._getAllNodes)
            print("INFO: "+str(len(all_nodes))+" nodes have been read")
            return all_nodes


if __name__ == "__main__":
    BDname = str(input("Enter database name: "))
    BDpassword = str(input("Enter database password: "))
    bd = Neo4jWorkspace("bolt://localhost:7687", "neo4j", BDpassword, BDname)
    nodes = bd.findAllNodes()
    G = Graph()
    print("Here's all nodes: ", end=" ")
    for A in nodes:
        print(A+"; ", end=" ")
        for B in nodes:
            if A != B:
                possible_length = bd.findRelation(A, B)
                L = possible_length.pop()
                if L is not None:
                    if bd.returnLabel(A).pop() == "Object" or bd.returnLabel(B).pop() == "Object":
                        L *= 3
                    G.add_edge(str(A), str(B), int(L))
    bd.close()
    print()

    pathStart = str(input("Input start point: "))
    pathEnd = str(input("Input end point: "))

    route = dijsktra(G, pathStart, pathEnd)

    t1 = ""
    t2 = ""
    t1 = route.pop()
    leng = 0
    print("PATH: ", t1, "->", end=" ")
    while len(route) > 1:
        t2 = route.pop()
        temp = bd.findRelation(t1, t2).pop()
        if temp is None:
            temp = bd.findRelation(t2, t1).pop()
        leng += int(temp)
        t1 = t2
        print(t2, "->", end=" ")
    t2 = route.pop()
    temp = bd.findRelation(t1, t2).pop()
    if temp is None:
        temp = bd.findRelation(t2, t1).pop()
    leng += int(temp)
    print(t2)
    print("PATH LENGTH: "+str(leng))

    print("INFO: Done!")

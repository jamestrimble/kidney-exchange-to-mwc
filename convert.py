import sys

class Edge(object):
    def __init__(self, line):
        self.src = int(line[0])
        self.tgt = int(line[1])
        self.wt = int(line[2])

class Cycle(object):
    def __init__(self, vv, wt):
        self.vv = vv[:]
        self.wt = wt

    def conflicts_with(self, other):
        return not set(self.vv).isdisjoint(other.vv)

    def __repr__(self):
        return "(" + ",".join(str(v) for v in self.vv) + ")" + str(self.wt)

class Chain(object):
    def __init__(self, ndd, vv, wt):
        self.ndd = ndd
        self.vv = vv[:]
        self.wt = wt

    def conflicts_with(self, other):
        if hasattr(other, 'ndd') and self.ndd==other.ndd:
            return False
        return not set(self.vv).isdisjoint(other.vv)

    def __repr__(self):
        return str(self.ndd) + "(" + ",".join(str(v) for v in self.vv) + ")" + str(self.wt)

class CycleFinder(object):
    def __init__(self, dpp_edge_lists, max_cycle):
        self.dpp_count = len(dpp_edge_lists)
        self.dpp_edge_lists = dpp_edge_lists
        self.max_cycle = max_cycle
        self.adjmat = [[False]*self.dpp_count for i in range(self.dpp_count)]
        for src, lst in enumerate(dpp_edge_lists):
            for edge in lst:
                self.adjmat[src][edge.tgt] = edge
        self.cycles = []

    def visit(self, c, weight):
        back_edge = self.adjmat[c[-1]][c[0]]
        if back_edge:
            self.cycles.append(Cycle(c, weight+back_edge.wt))
        if len(c) < max_cycle:
            for e in self.dpp_edge_lists[c[-1]]:
                if e.tgt > c[0]:
                    self.visit(c + [e.tgt], weight+e.wt)

    def find_cycles(self):
        if self.max_cycle==0: return self.cycles
        for i in range(self.dpp_count):
            self.visit([i], 0)
        return self.cycles

class ChainFinder(object):
    def __init__(self, dpp_edge_lists, ndd_edge_lists, max_chain):
        self.dpp_count = len(dpp_edge_lists)
        self.dpp_edge_lists = dpp_edge_lists
        self.ndd_count = len(ndd_edge_lists)
        self.ndd_edge_lists = ndd_edge_lists
        self.max_chain = max_chain
        self.chains = []

    def visit(self, ndd, vv, weight):
        self.chains.append(Chain(ndd, vv, weight))
        if len(vv) < max_chain:
            for e in self.dpp_edge_lists[vv[-1]]:
                self.visit(ndd, vv + [e.tgt], weight+e.wt)

    def find_chains(self):
        print(self.max_chain)
        if self.max_chain<1: return self.chains
        for i in range(self.ndd_count):
            for edge in self.ndd_edge_lists[i]:
                self.visit(i, [edge.tgt], edge.wt)
        return self.chains

def convert(lines, max_cycle, max_chain):
    for i, line in enumerate(lines):
        if line[0]=="-1":
            break

    dpp_lines = lines[:i+1]
    ndd_lines = lines[i+1:]

    dpp_count, dpp_edge_count = int(dpp_lines[0][0]), int(dpp_lines[0][1])
    dpp_edges = [Edge(line) for line in dpp_lines[1:dpp_edge_count+1]]
    dpp_edge_lists = [[] for i in range(dpp_count)]
    for edge in dpp_edges:
        dpp_edge_lists[edge.src].append(edge)

    ndd_count, ndd_edge_count = int(ndd_lines[0][0]), int(ndd_lines[0][1])
    ndd_edges = [Edge(line) for line in ndd_lines[1:ndd_edge_count+1]]
    ndd_edge_lists = [[] for i in range(ndd_count)]
    for edge in ndd_edges:
        ndd_edge_lists[edge.src].append(edge)

    cycles = CycleFinder(dpp_edge_lists, max_cycle).find_cycles()
    chains = ChainFinder(dpp_edge_lists, ndd_edge_lists, max_chain).find_chains()
#    print(len(cycles), len(chains), len(cycles)+len(chains))

    exchanges = cycles + chains
    g_edges = []
    for i in range(len(exchanges) - 1):
        for j in range(i+1, len(exchanges)):
            if not exchanges[i].conflicts_with(exchanges[j]):
                g_edges.append((i, j))

    print("p edge {} {}".format(len(exchanges), len(g_edges)))
    for i, exch in enumerate(exchanges):
        print("n {} {}".format(i+1, exch.wt))
    for edge in g_edges:
        print("e {} {}".format(edge[0]+1, edge[1]+1))

if __name__=="__main__":
    max_cycle = int(sys.argv[1])
    max_chain = int(sys.argv[2])
    lines = [line.strip().split() for line in sys.stdin.readlines()]
    convert(lines, max_cycle, max_chain)

import random
import sys

class Edge(object):
    def __init__(self, line):
        self.src = int(line[0])
        self.tgt = int(line[1])
        self.wt = int(line[2])

class Cycle(object):
    def __init__(self, vv, wt):
        self.vv = vv[:]
        self.vv_set = set(self.vv)
        self.wt = wt

    def conflicts_with(self, other):
        return not self.vv_set.isdisjoint(other.vv_set)

    def participant_ids(self, num_dpps):
        return self.vv[:]

    def __repr__(self):
        return "(" + ",".join(str(v) for v in self.vv) + ")" + str(self.wt)

class Chain(object):
    def __init__(self, ndd, vv, wt):
        self.ndd = ndd
        self.vv = vv[:]
        self.vv_set = set(self.vv)
        self.wt = wt

    def conflicts_with(self, other):
        if hasattr(other, 'ndd') and self.ndd==other.ndd:
            return True
        return not self.vv_set.isdisjoint(other.vv_set)

    def participant_ids(self, num_dpps):
        return self.vv[:] + [self.ndd+num_dpps]

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
        if self.max_chain<1: return self.chains
        for i in range(self.ndd_count):
            for edge in self.ndd_edge_lists[i]:
                self.visit(i, [edge.tgt], edge.wt)
        return self.chains

def create_p_to_e(remaining_exchanges, e_to_p, participant_count):
    p_to_e = [[] for _ in range(participant_count)]
    for exch_id in remaining_exchanges:
        participant_ids = e_to_p[exch_id]
        for p_id in participant_ids:
            p_to_e[p_id].append(exch_id)
    return p_to_e

def bound(p_to_e, exchanges):
    return sum(exchanges[l[0]].wt if len(l) else 0 for l in p_to_e)

def dominated_by_one(pp, p_to_e, e_to_p, heavier_exch_id):
    for p in e_to_p[heavier_exch_id]:
#        print len(p_to_e[p]), (p not in pp)
        if p not in pp and len(p_to_e[p]) > 1:
            return False
#    print pp, pp_in_heavier_exch
    return True

def dominated(exch_id, p_to_e, e_to_p, heavier_exchanges, adjmat):
    pp = e_to_p[exch_id]
    adjrow = adjmat[exch_id]
    for i in heavier_exchanges:
        if not adjrow[i] and dominated_by_one(pp, p_to_e, e_to_p, i):
            return True
    return False

def remove_dominated(remaining_exchs, p_to_e, e_to_p, adjmat):
    kept_exchanges = []
    for exch_id in remaining_exchs:
        if not dominated(exch_id, p_to_e, e_to_p, kept_exchanges, adjmat):
            kept_exchanges.append(exch_id)
    return kept_exchanges

class Incumbent(object):
    def __init__(self, exchanges):
        self.value = []
        self.exchanges = exchanges
    
    def set(self, value):
        self.value = value[:]

    def total_wt(self):
        return sum(self.exchanges[e].wt for e in self.value)

    def get(self):
        return self.value[:]

# are the exchange with indices e0 and e1 compatible?
# (Two exchanges are compatible if they don't share any participants)
def compatible(e0, e1, e_to_p):
    pp0 = e_to_p[e0]
    pp1 = e_to_p[e1]
    return not any(p in pp1 for p in pp0)

def total_wt(exch_ids, exchanges):
    return sum(exchanges[e].wt for e in exch_ids)

nodes = 0

def has_conflicts(exchange_id, e_to_p, p_to_e):
    for p in e_to_p[exchange_id]:
        if len(p_to_e[p]) > 1:
            return True
    return False

def new_bound(remaining_exchanges, adjmat, exchanges):
    bound = 0
    still_uncoloured = remaining_exchanges
    while len(still_uncoloured):
        uncoloured = still_uncoloured
        still_uncoloured = []
        coloured = []
        for exch in uncoloured:
            adjrow = adjmat[exch]
            if not any(adjrow[coloured_exch] for coloured_exch in coloured):
                coloured.append(exch)
            else:
                still_uncoloured.append(exch)
        bound += exchanges[coloured[0]].wt
    return bound

def select_exchange(remaining_exchanges, e_to_p, p_to_e):
    best = -1
    best_list_len = -1#len(remaining_exchanges) + 1
    for exch in remaining_exchanges:
        if not has_conflicts(exch, e_to_p, p_to_e):
            return exch, False
        listlen = sum(len(p_to_e[p]) for p in e_to_p[exch])
        if listlen > best_list_len:
            best_list_len = listlen
            best = exch
    return best, True

def search(incumbent, current, remaining_exchanges, e_to_p, participant_count,
        exchanges, adjmat, ub_on_bound):
    global nodes
    nodes += 1
    
    if len(current)==0:
        print "*", len(remaining_exchanges), ub_on_bound
#    print sorted([len(l) for l in p_to_e])
#    print "Incumbent:", incumbent.total_wt(), "      ", incumbent.get()
#    print "Bound:", bound(p_to_e, exchanges)

    tot_wt = total_wt(current, exchanges)

    if tot_wt > incumbent.total_wt():
        incumbent.set(current)
        print "New incumbent", incumbent.total_wt()

    incumbent_wt = incumbent.total_wt()

#    print bound(p_to_e, exchanges), new_bound(remaining_exchanges, adjmat, exchanges)
#    if tot_wt + bound(p_to_e, exchanges) <= incumbent.total_wt():
#        return
    bound = min(ub_on_bound, tot_wt + new_bound(remaining_exchanges, adjmat, exchanges))

    if bound <= incumbent_wt:
        return

    p_to_e = create_p_to_e(remaining_exchanges, e_to_p, participant_count)
    chosen_exch, has_conf = select_exchange(remaining_exchanges, e_to_p, p_to_e)

    remaining_exchanges_using_chosen = [e for e in remaining_exchanges if adjmat[e][chosen_exch]]
#    remaining_exchanges_using_chosen = remove_dominated(remaining_exchanges_using_chosen, p_to_e, e_to_p, adjmat)
    search(incumbent, current+[chosen_exch], remaining_exchanges_using_chosen,
            e_to_p, participant_count, exchanges, adjmat, bound)
    
    if has_conf:
        remaining_exchanges_without_chosen = [exch for exch in remaining_exchanges if exch != chosen_exch]
#        remaining_exchanges_without_chosen = remove_dominated(remaining_exchanges_without_chosen, p_to_e, e_to_p, adjmat)
        search(incumbent, current, remaining_exchanges_without_chosen,
                e_to_p, participant_count, exchanges, adjmat, bound)


def solve(lines, max_cycle, max_chain):
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

    # Participants are DPPs numbered [0...dpp_count) and
    # NDDs numbered [dpp_count...dpp_count+ndd_count)
    participant_count = dpp_count + ndd_count

    exch_count_per_participant = [ ]

    exchanges = cycles + chains
    e_to_p_TMP = [exch.participant_ids(dpp_count) for exch in exchanges]
    exchs_TMP = range(len(exchanges))
    p_to_e_TMP = create_p_to_e(exchs_TMP, e_to_p_TMP, participant_count)
    exchanges.sort(key=lambda exch:
            (exch.wt, sum(len(p_to_e_TMP[p]) for p in exch.participant_ids(dpp_count))), reverse=True)
    print "Exchange count", len(exchanges)

#    for exch in exchanges:
#        print exch

    # exchange id to participants
    e_to_p = [exch.participant_ids(dpp_count) for exch in exchanges]

    remaining_exchanges = range(len(exchanges))

    # participant id to exchanges
    p_to_e = create_p_to_e(remaining_exchanges, e_to_p, participant_count)

#    print e_to_p
#    print p_to_e
#
#    print sorted([len(l) for l in p_to_e])
#    print "Bound:", bound(p_to_e, exchanges)

##    incumbent = Incumbent(exchanges)
##    current = []
##    search(incumbent, current, remaining_exchanges, p_to_e, e_to_p, participant_count,
##            exchanges, adjmat)

    adjmat = [[compatible(i, j, e_to_p) for j in range(len(exchanges))] for i in range(len(exchanges))]

    reduced_remaining_exchanges = remove_dominated(remaining_exchanges, p_to_e, e_to_p, adjmat)
    p_to_e = create_p_to_e(reduced_remaining_exchanges, e_to_p, participant_count)
#    print sorted([len(l) for l in p_to_e])
#    print "Bound:", bound(p_to_e, exchanges)

    incumbent = Incumbent(exchanges)
    current = []
    print "New bound:", new_bound(reduced_remaining_exchanges, adjmat, exchanges)
    search(incumbent, current, reduced_remaining_exchanges, e_to_p, participant_count,
            exchanges, adjmat, 999999999)

    print "Incumbent", incumbent.total_wt(), incumbent.get()
    print "Nodes", nodes
#    g_edges = []
#    for x in range(len(reduced_remaining_exchanges) - 1):
#        i = reduced_remaining_exchanges[x]
#        for y in range(i+1, len(reduced_remaining_exchanges)):
#            j = reduced_remaining_exchanges[y]
#            if not exchanges[i].conflicts_with(exchanges[j]):
#                g_edges.append((i, j))
#
#    print("p edge {} {}".format(len(exchanges), len(g_edges)))
#    for i, exch in enumerate(exchanges):
#        print("n {} {}".format(i+1, exch.wt))
#    for edge in g_edges:
#        print("e {} {}".format(edge[0]+1, edge[1]+1))

if __name__=="__main__":
    max_cycle = int(sys.argv[1])
    max_chain = int(sys.argv[2])
    lines = [line.strip().split() for line in sys.stdin.readlines()]
    solve(lines, max_cycle, max_chain)

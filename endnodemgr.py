from candinode import CandiNode
from tnode import TNode
from node12 import Node12


class EndNodeManager:
    limit = 10

    def __init__(self, endnode, tail_sh):
        self.endnode = endnode  # satnode with empty vkdic
        self.sh = tail_sh       # satnode.next_sh
        self.candis = []
        self.build_candis()
        self.chdic = {}
        self.sats = []

    def build_candis(self):
        candinode = CandiNode(self.endnode)
        _end = False
        while not _end:
            _end = candinode.find_candi(self.candis)
            # break
        x = 1

    def spawn(self, candi):
        hsat = {}
        node_name = '-'.join(candi)
        tnodes = [TNode.repo[tname] for tname in candi]
        for tn in tnodes:
            hsat.update(tn.hsat)
        print(f'process {node_name}')
        node = Node12(node_name, self, self.sh.clone(), hsat)
        for tn in tnodes:
            if not node.add_filtered_vkdic(tn.vkdic, tn.sh):
                break
        if node.valid:
            # print(f'{node_name} added')
            self.chdic[node_name] = node
            node.spawn()
        else:
            print(f'{node_name} failed')

    def solve(self):
        print(f'EndNodeManager solve starting...')
        for candi in self.candis:
            self.spawn(candi)
        return self.sats

    def resolve0(self):
        for can in self.candis:
            self.convert_sat(can, endnode)
            if self.done:  # if limit reached, done==True.
                break

    def convert_sat(self, candi, endnode):
        filter_sat = {}
        tnodes = [TNode.repo[tname] for tname in candi]
        for tn in tnodes:
            filter_sat.update(tn.hsat)
        print(f'solving {candi}')
        if endnode.solve(filter_sat, tnodes):
            self.sats += endnode.sats
        else:
            print(f'path: {candi} failed generating sat.')
        self.done = len(self.sats) >= self.limit

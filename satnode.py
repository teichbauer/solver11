from basics import topbits, print_json
from satholder import SatHolder
from TransKlauseEngine import TxEngine
# from endnodemgr import EndNodeManager
from tnode import TNode
from pathmgr import PathManager


class SatNode:
    debug = False
    maxnov = 0

    def __init__(self, parent, sh, vkm):
        self.parent = parent
        self.sh = sh
        self.vkm = vkm
        self.nov = vkm.nov
        self.sats = None
        self.topbits = topbits(self.nov, 3)
        self.next = None
        self.done = False
        self.prepare()

    def is_top(self):
        return self.nov == SatNode.maxnov

    def solve(self):
        return PathManager.sats

    def prepare(self):
        choice = self.vkm.bestchoice()
        bvks = choice["bestkey"]
        print(f'bvk: {bvks}')
        for kn in bvks:
            xbvk = self.vkm.vkdic[kn]
            print(f'{xbvk.dic}')
        self.bvk = self.vkm.vkdic[choice['bestkey'][0]]
        if self.topbits != choice['bits']:  # the same as self.bvk.bits:
            self.tx = TxEngine(self.bvk)
            self.sh.transfer(self.tx)
            self.tx_vkm = self.vkm.txed_clone(self.tx)
        else:
            self.tx_vkm = self.vkm.clone()
        self.tail_varray = self.sh.spawn_tail(3)
        self.next_sh = SatHolder(self.tail_varray[:])
        self.sh.cut_tail(3)

        self.vk12dic = {}  # store all vk12s, all tnode's vkdic ref to here
        # after tx_vkm.morph, tx_vkm only has (.vkdic) vk3 left, if any
        # and tx_vkm.nov decreased by 3, used in spawning self.next
        self.chdic = self.tx_vkm.morph(self)
        ks = [f'{self.nov}.{k}' for k in self.chdic.keys()]
        print(f'keys: {ks}')
        self.make_paths()
    # end of def prepare(self):

    def spawn(self):
        # print(f'snode-nov{self.nov}')
        # after morph, vkm.vkdic only have vk3s left, if any
        if len(self.chdic) == 0:
            self.done = True
            return None
        else:
            self.next = SatNode(self, self.next_sh.clone(), self.tx_vkm)
            return self.next

    def make_paths(self):
        if not self.parent:  # do nothing for top-level snode
            return
        self.done = len(self.tx_vkm.vkdic) == 0
        # collect higher-chs, and the ones being refed by this snode
        higher_vals_inuse = set([])
        dels = []   # for collecting tnode with no path
        for val, tnode in self.chdic.items():
            tnode.pthmgr = PathManager(tnode, self.done)
            if len(tnode.pthmgr.dic) == 0:
                dels.append(tnode)
            else:
                high_vals = [int(k[1].split('.')[1]) for k in tnode.pthmgr.dic]
                higher_vals_inuse.update(high_vals)
        # clean-up ch-tnodes, if its pthmgr.dic is empty
        for tnode in dels:
            self.chdic.pop(tnode.val)
            TNode.repo.pop(tnode.name)
        # clean-up higher-chs not being used by any tnode
        self.parent.trim_chs(higher_vals_inuse)

    def trim_chs(self, used_vals):
        ''' the chdic keys not in used_vals(a set), will be deleted. if this
            changs used val-set of parent level, recursiv-call on parent '''
        s = set(self.chdic.keys())
        if s != used_vals:
            delta = s - used_vals
            for v in delta:
                tn = self.chdic.pop(v, None)
                if tn:
                    TNode.repo.pop(tn.name)
            if self.parent:
                # recursive call of parent.trim_chs
                higher_vals_inuse = set([])
                for tn in self.chdic.values():
                    vs = [int(k.split('-')[1]) for k in tn.pthmgr.dic]
                    higher_vals_inuse.update(vs)
                self.parent.trim_chs(higher_vals_inuse)

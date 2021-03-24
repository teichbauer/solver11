from basics import topbits, print_json
from satholder import SatHolder
from TransKlauseEngine import TxEngine
from endnodemgr import EndNodeManager
from tnode import TNode


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

    def prepare(self):
        choice = self.vkm.bestchoice()
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
        self.restrict_chs()
        if self.debug:
            vk3cnt = len(self.vkm.vkdic)
            restvk3cnt = len(self.tx_vkm.vkdic)
            vk12cnt = len(self.vk12dic)
            chvals = list(self.chdic.keys())
            sharray = self.sh.varray
            m = f'sn{self.nov}: {vk3cnt} -> {restvk3cnt}: {vk12cnt}, '
            m += f'{choice["bestkey"]}, chs:{chvals}, sh:{sharray}'
            print(m)
        x = 1
    # end of def prepare(self):

    def spawn(self):
        print(f'snode-nov{self.nov}')
        if self.done:
            return self.sats
        # after morph, vkm.vkdic only have vk3s left, if any
        if len(self.chdic) == 0:
            self.sats = None
            self.done = True
            return None
        if len(self.tx_vkm.vkdic) == 0:
            self.next = EndNodeManager(self, self.next_sh)
        else:
            self.next = SatNode(self, self.next_sh.clone(), self.tx_vkm)
        return self.next

    def restrict_chs(self):
        ''' for every child C in chdic, check which children of 
            self.satnode.chdic, are compatible with C, (allows vksat)
            build a pvs containing child-keys of the children that are 
            compatible, set chdic[val].pvs
            '''
        if not self.parent:
            return
        del_tnodes = []
        hvs = list(self.parent.chdic.keys())
        htcnt = {hv: 0 for hv in hvs}
        for tnode in self.chdic.values():
            tnode.pathdic = {}
            for hv in hvs:
                tn = self.parent.chdic[hv]
                if tn.check_sat(tnode.hsat, True):
                    vk12dic = tnode.find_path_vk12dic(tn)
                    if vk12dic:
                        tnode.pathdic[tn.name] = vk12dic
                        htcnt[hv] += 1
            if len(tnode.pathdic) == 0:
                del_tnodes.append(tnode)
        for tnode in del_tnodes:
            self.chdic.pop(tnode.val, None)
            TNode.repo.pop(tnode.name, None)

        for hv, sm in htcnt.items():
            if sm == 0:
                t = self.parent.chdic.pop(hv, None)
                if t:
                    TNode.repo.pop(t.name, None)
        x = 1

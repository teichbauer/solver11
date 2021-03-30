from basics import topbits, filter_sdic, oppo_binary
from TransKlauseEngine import TxEngine
from vk12mgr import VK12Manager
from satholder import SatHolder
from tnode import TNode


class Node12:
    def __init__(self, val, parent, sh, hsat, vkm=None):
        self.parent = parent
        self.hsat = hsat
        self.nov = sh.ln
        if vkm:
            self.vkmgr = vkm
        else:
            self.vkmgr = VK12Manager(self.nov)
        self.val = val
        self.chdic = {}
        self.sh = sh
        self.done = self.check_done()

    def check_done(self):
        if self.nov == 0:
            return True
        ln = len(self.vkmgr.vkdic)
        if ln == 0:
            self.tsat = {}
            for v in self.sh.varray:
                self.tsat[v] = 2
            return True
        elif ln == 1:
            self.tsat = {}
            vk = list(self.vkmgr.vkdic.values())[0]
            if vk.nob == 1:
                b = vk.bits[0]
                v = vk.dic[b]
                d = {self.sh.varray[b]: oppo_binary(v)}
                for v in self.sh.varray:
                    if v in d:
                        self.tsat[v] = d[v]
                    else:
                        self.tsat[v] = 2
                return True
            else:   # vk.nob == 2
                b0, b1 = vk.bits
                var0 = self.sh.varray[b0]
                var1 = self.sh.varray[b1]
                value0 = vk.dic[b0]
                value1 = vk.dic[b1]
                tsat0 = {}
                for v in self.sh.varray:
                    if v == var0:
                        tsat0[v] = oppo_binary(value0)
                    elif v == var1:
                        tsat[v] = value1
                    else:
                        tsat[v] = 2
                tsat1 = tsat0.copy()
                tsat1[var0] = value0
                tsat1[var1] = oppo_binary(value1)
                self.tsat = [tsat0, tsat1]
                return True
        return False

    def collect_sat(self, tsat=None):
        if tsat == None:
            self.collect_sat(self.tsat)
        else:
            if type(tsat) == type([]):
                for ts in tsat:
                    self.collect_sat(ts)
            else:
                sat = tsat.copy()
                sat.update(self.hsat)
                if isinstance(self.parent, Node12):
                    self.parent.collect_sat(sat)
                else:  # parent is PathManager with a class-var(list).sats
                    pthnames = self.path_name[:]
                    while len(pthnames) > 0:
                        tn = TNode.repo[pthnames.pop(0)]
                        sat.update(tn.hsat)
                    self.parent.sats.append(sat)

    def spawn(self):
        self.bvk = self.vkmgr.pick_bvk()
        self.topbits = topbits(self.nov, self.bvk.nob)
        if self.bvk.bits != self.topbits:  # tx needed?
            self.tx = TxEngine(self.bvk)
            self.sh.transfer(self.tx)
            tx_vkdic = self.tx.trans_vkdic(self.vkmgr.vkdic)
        else:
            tx_vkdic = self.vkmgr.vkdic
        self.tail_varray = self.sh.spawn_tail(self.bvk.nob)
        self.next_sh = SatHolder(self.tail_varray[:])
        self.sh.cut_tail(self.bvk.nob)

        # generate dic of Node12 instances, keyed by val
        self.chdic = self.vkmgr.morph(self, self.bvk.nob)

        vals = list(self.chdic.keys())
        for val in vals:
            if self.chdic[val].done:
                self.chdic[val].collect_sat()
            else:
                self.chdic[val].spawn()

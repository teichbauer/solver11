from basics import verify_sat, oppo_binary
from restrict import Restrict
from vk12mgr import VK12Manager


class TNode:
    # repo holds all tnode, under its name
    repo = {}   # {<tnode-name>:<tnode-instance>,...}

    def __init__(self, vk12dic, holder_snode, val):
        self.vkdic = vk12dic
        self.val = val
        self.holder = holder_snode
        self.sh = holder_snode.next_sh
        self.name = f'{self.holder.nov}.{val}'
        self.hsat = holder_snode.sh.get_sats(val)
        self._sort12()
        self.restrict = Restrict(self.sh)
        self.bmap = {}
        self.set_bmap()
        self._proc_vk1s()
        self._proc_vk2s()
        self.check_state()
        # -----------
        # self.pvs will be assigned by snode.restrict. it is a list of
        # ch-keys of highter-nov tnodes, that are compatible with this tnode.

    def check_state(self):
        self.state = 0
        dic = {}
        for p in self.restrict.conditional_conflicts:
            if p[0] in dic:
                if p[1] != dic[p[0]]:
                    self.state = -1
                    break
            else:
                dic[p[0]] = p[1]

    def _proc_vk1s(self):
        kns = self.kn1s[:]
        while len(kns) > 0:
            kn = kns.pop()
            vk = self.vkdic.get(kn, None)
            if not vk:
                continue  # kn may has been popped out from vkdic
            bit = vk.bits[0]
            allkns = list(self.vkdic.keys())
            allkns.remove(kn)
            for kx in allkns:
                vkx = self.vkdic[kx]
                if bit in vkx.bits:
                    if vkx.dic[bit] == vk.dic[bit]:
                        self._remove_kn(kx)
            # a vk1 makes a conditional-conflict entry
            self.restrict.add_cconflict((bit, vk.dic[bit]))
    # end of _proc_vk1s ----------------------------------------

    def _proc_vk2s(self):
        if len(self.kn2s) == 0:
            return
        sames = []
        kns = self.kn2s[:]
        vk = self.vkdic[kns.pop()]
        bs = vk.bits
        while len(kns) > 0:
            for kn in kns:
                vkx = self.vkdic[kn]
                if vk.bits == vkx.bits:
                    if vk.dic[bs[0]] == vkx.dic[bs[0]]:
                        if vk.dic[bs[1]] == vkx.dic[bs[1]]:
                            sames.append(vkx.kname)
                        else:
                            self.restrict.add_cconflict((bs[0], vk.dic[bs[0]]))
                    else:  # bs[0]: diff values
                        if vk.dic[bs[1]] == vkx.dic[bs[1]]:
                            self.restrict.add_cconflict((bs[1], vk.dic[bs[1]]))
            vk = self.vkdic[kns.pop()]
            bs = vk.bits
        # kick out sames
        for kn in sames:
            self._remove_kn(kn)
    # end of _proc_vk2s ----------------------------------------

    def _remove_kn(self, kn):
        vk = self.vkdic.pop(kn, None)
        if vk:
            if vk.nob == 1:
                if kn in self.kn1s:
                    self.kn1s.remove(kn)
            elif vk.nob == 2:
                if kn in self.kn2s:
                    self.kn2s.remove(kn)
            for b in vk.bits:
                index = -1
                for ind, t in enumerate(self.bmap[b]):
                    if t[0] == kn:
                        index = ind
                        break
                if index > -1:
                    self.bmap[b].pop(index)
    # end of _remove_kn ----------------------------------------

    def _sort12(self):
        self.kn1s = []
        self.kn2s = []
        for kn, vk in self.vkdic.items():
            if vk.nob == 1:
                self.kn1s.append(kn)
            else:
                self.kn2s.append(kn)

    def set_bmap(self):
        for kn, vk in self.vkdic.items():
            for b, v in vk.dic.items():
                lst = self.bmap.setdefault(b, [])
                lst.append((kn, v))
    # end of set_bmap ----------------------------------------

    def check_sat(self, sdic, reverse_sh=False):
        if reverse_sh:
            return verify_sat(self.vkdic, self.sh.reverse_sdic(sdic))
        return verify_sat(self.vkdic, sdic)

    def find_candis(self, hsats, psatnode, pvs):
        sdic = {}
        for sat in hsats[1:]:
            sdic.update(sat)

        for ch in psatnode.chdic.values():
            hsat = ch[hsat]

            candi = hsats[:]
            candi.insert(0, ch['hsat'])
            succ = ch['tnode'].check_sat()

        succ = True
        i = 1
        while succ and i < len(hsats):
            succ = self.check_sat(hsats[i])
            i += 1
        if succ:
            if psatnode == None:
                return []

        for ch in psatnode.chdic.values():
            candi = [ch['hsat'], hsat]

    def find_path_vk12m(self, ptnode):
        bmap = ptnode.sh.bit_tx_map(self.sh)
        ksat = ptnode.sh.reverse_sdic(self.hsat)  # ? not used
        vk12m = VK12Manager(self.holder.nov)
        # adding all vk-residues from ptnode (vk cut by hsat) to vk12m
        for kn, pvk in ptnode.vkdic.items():
            vk12 = pvk.partial_hit_residue(ksat, bmap)
            if vk12:
                vk12m.add_vk(vk12)
        # adding all vks from self.vkdic to vk12m
        for kn, vk in self.vkdic.items():
            vk12m.add_vk(vk)
        return vk12m

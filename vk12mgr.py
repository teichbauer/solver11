from vklause import VKlause
from basics import topvalue, topbits, oppo_binary, topbits_coverages
from TransKlauseEngine import TxEngine


class VK12Manager:
    def __init__(self, nov, vkdic=None):
        self.nov = nov
        self.reset()  # set vkdic, bdic, kn1s, kn2s
        if vkdic and len(vkdic) > 0:
            self.vkdic = vkdic

    def reset(self):
        self.bdic = {}
        self.vkdic = {}
        self.kn1s = []
        self.kn2s = []
        self.valid = True  # no sat possible/total hit-blocked
        self.info = {}

    def clone(self):
        vk12m = VK12Manager(self.nov)
        for vk in self.vkdic.values():
            vk12m.add_vk(vk.clone())
        return vk12m

    def add_vkdic(self, vkdic):
        for vk in vkdic.values():
            self.add_vk(vk)

    def add_vk(self, vk):
        if vk.nob == 1:
            bit = vk.bits[0]
            if bit in self.bdic and len(self.bdic[bit]) > 0:
                kns = self.bdic[bit][:]
                for kn in kns:
                    if kn in self.kn1s:
                        if self.vkdic[kn].dic[bit] != vk.dic[bit]:
                            self.valid = False
                            msg = f'vk1:{vk.kname} vs {kn}: valid: {self.valid}'
                            self.info[vk.kname] = msg
                            print(msg)
                            return False
                        else:  # self.vkdic[kn].dic[bit] == vk.dic[bit]
                            msg = f'{vk.kname} duplicated with {kn}'
                            self.info[vk.kname] = msg
                            print(msg)
                            return False
                    elif kn in self.kn2s:
                        if self.vkdic[kn].dic[bit] == vk.dic[bit]:
                            # a vk2 has the same v on this bit: remove vk2
                            msg = f'{vk.kname} removes {kn}'
                            self.info[vk.kname] = msg
                            print(msg)
                            self.kn2s.remove(kn)
                            vkn = self.vkdic.pop(kn)
                            for b in vkn.bits:
                                self.bdic[b].remove(kn)
            # add the vk
            self.vkdic[vk.kname] = vk
            self.kn1s.append(vk.kname)
            self.bdic.setdefault(bit, []).append(vk.kname)
            return True
        elif vk.nob == 2:
            # if an existin vk1 covers vk?
            for kn in self.kn1s:
                b = self.vkdic[kn].bits[0]
                if b in vk.bits and self.vkdic[kn].dic[b] == vk.dic[b]:
                    # vk not added. but valid is this still
                    msg = f'{vk.kname} blocked by {kn}'
                    self.info[vk.kname] = msg
                    print(msg)
                    return False
            # find vk2s withsame bits
            pair_kns = []
            for kn in self.kn2s:
                if self.vkdic[kn].bits == vk.bits:
                    pair_kns.append(kn)
            bs = vk.bits
            for pk in pair_kns:
                pvk = self.vkdic[pk]
                if vk.dic[bs[0]] == pvk.dic[bs[0]]:
                    if vk.dic[bs[1]] == pvk.dic[bs[1]]:
                        msg = f'{vk.kname} douplicated with {kn}'
                        self.info[vk.kname] = msg
                        print(msg)
                        return False  # vk not added
                    else:  # b0: same value, b1 diff value
                        msg = f'{vk.kname} + {pvk.kname}: {pvk.kname}->vk1'
                        self.info[vk.kname] = msg
                        print(msg)
                        # remove pvk
                        self.vkdic.pop(pvk.kname)       # from vkdic
                        self.kn2s.remove(pvk.kname)     # from kn2s
                        for b in bs:                    # from bdic
                            self.bdic[b].remove(pvk.kname)
                        pvk.drop_bit(bs[1])
                        self.add_vk(pvk)  # validity made when add pvk as vk1
                        return False   # vk not added.
                else:  # b0 has diff value
                    if vk.dic[bs[1]] == pvk.dic[bs[1]]:
                        # b1 has the same value
                        msg = f'{vk.kname} + {pvk.kname}: {pvk.kname}->vk1'
                        self.info[vk.kname] = msg
                        print(msg)
                        # remove pvk
                        self.vkdic.pop(pvk.kname)       # from vkdic
                        self.kn2s.remove(pvk.kname)     # from vk2s
                        for b in bs:                    # from bdic
                            self.bdic[b].remove(pvk.kname)

                        # add pvk back as vk1, after dropping bs[1]
                        pvk.drop_bit(bs[0])
                        return self.add_vk(pvk)
                        return False    # vk not added
                    else:  # non bit from vk has the same value as pvk's
                        pass
            for b in bs:
                self.bdic.setdefault(b, []).append(vk.kname)
            self.kn2s.append(vk.kname)
            self.vkdic[vk.kname] = vk
            return True

    def pick_bvk(self):
        if len(self.kn1s) > 0:
            # pick the one with top-bit. Or the first one
            i = 0
            vk = self.vkdic[self.kn1s[i]]
            while i < len(self.kn1s) and vk.bits[0] != self.nov - 1:
                i += 1
                if i < len(self.kn1s):
                    vk = self.vkdic[self.kn1s[i]]
            return vk
        else:
            # pick the vk2 with max bit-sum
            kn = self.kn2s[0]
            if len(self.kn2s) > 1:
                bsum = sum(self.vkdic[kn].bits)
                for kx in self.kn2s[1:]:
                    xsum = sum(self.vkdic[kx].bits)
                    if bsum < xsum:
                        kn = kx
                        bsum = xsum
            return self.vkdic[kn]

    def morph(self, n12, nob):
        n12.vk12dic = {}
        chs = {}
        excl_cvs = set([])
        self.nov -= nob  # top nob bit(s) will be cut off

        tdic = {}
        for kn, vk in self.vkdic.items():
            cvr, odic = topbits_coverages(vk, n12.topbits)
            vk12 = vk.clone(n12.topbits)  # if no bit left: vk12 == None
            if not vk12:  # vk is within topbits, no bit left
                for v in cvr:  # collect vk's cover-value
                    excl_cvs.add(v)
            else:  # a non-empty vk12 exists, with bits outside topbits
                n12.vk12dic[kn] = vk12
                tdic.setdefault(tuple(cvr), []).append(vk12)

        for val in range(2 ** nob):
            if val in excl_cvs:
                continue
            sub_vk12dic = {}
            for cvr in tdic:
                if val in cvr:  # touched kn/kv does have outside bit
                    vks = tdic[cvr]
                    for vk in vks:
                        sub_vk12dic[vk.kname] = vk
            node = n12.__class__(
                val,                    # val as node.name
                n12,                    # n12 is parent-node
                n12.next_sh,            # sh
                n12.sh.get_sats(val))   # val turns to hsat based on topbits
            node.add_vkdic_and_checkdone(sub_vk12dic)
            # vkmgr adds sub_vk12dic, it can turn invalid
            if node.vkmgr.valid:
                chs[val] = node
        return chs  # for making chdic with tnodes

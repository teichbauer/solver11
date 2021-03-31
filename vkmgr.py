from basics import topbits_coverages, print_json
from vklause import VKlause
from tnode import TNode
# from endnodemgr import EndNodeManager


class VKManager:
    def __init__(self, vkdic, nov, initial=False):
        self.vkdic = vkdic
        self.nov = nov
        if initial:
            self.make_bdic()

    def clone(self):
        vkdic = {kn: vk.clone() for kn, vk in self.vkdic.items()}
        return VKManager(vkdic, self.nov, True)

    def printjson(self, filename):
        print_json(self.nov, self.vkdic, filename)

    def make_bdic(self):
        self.bdic = {b: set([]) for b in range(self.nov)}
        for kn, vk in self.vkdic.items():
            for b in vk.dic:
                self.bdic[b].add(kn)

    def txed_clone(self, tx):
        vkdic = tx.trans_vkdic(self.vkdic)
        return VKManager(vkdic, self.nov)

    # def morph(self, snode, vk12dic):
    def morph(self, snode):
        ''' only called on a txed (best-vks condensed to top 3 bits) clone.
            ----------------------------------------------------------------
            After cut-off top 3 bits, there will be 3 groups of vks:
            1. the vks with no bits left-over. They are within the top bits
               the values within 3 bits, covered by these vks (excl_cvs), will
               be taken away from 2**3 values.
               rest of 2**3 values are the vals set into chdic/vk12dic
               These vks will be taken off vkdic
            2. the vks with no bit in the top bit - they remain 3-bit vks
               they will have nov -= 3. They remain in vkdic
            3. vks with bit in, and out of top bits. After cut, they will be
               vk12. They are put into tdic, keyed by the top-bit value they
               cover
            '''
        chs = {}  # {<cvr-val>: {kn, ..},..}
        excl_cvs = set([])
        kns = list(self.vkdic.keys())
        self.nov -= 3  # top 3 bits will be cut off

        # tdic: dict for every touched vk: all are vk12, vk3 are in self.vkdic
        # key: tuple of covered-values, value: list of vks that
        # have the same covered-values
        # tdic for fill-in snode.vk12dic, and subset(vks) of it for tnode
        tdic = {}
        for kn in kns:
            vk = self.vkdic[kn]
            cvr, odic = topbits_coverages(vk, snode.topbits)
            ln = len(odic)
            if ln < vk.nob:  #
                self.vkdic.pop(kn)
                if ln == 0:  # vk is within topbits, no bit left
                    for v in cvr:  # collect vk's cover-value
                        excl_cvs.add(v)
                else:  # vk has 1 / 2 bits cut away by topbits
                    if kn in snode.vk12dic:
                        vk12 = snode.vk12dic[kn]
                    else:
                        vk12 = VKlause(kn, odic, self.nov)
                        snode.vk12dic[kn] = vk12
                    tdic.setdefault(tuple(cvr), []).append(vk12)
            else:  # vk.nob == ln: this vk3 remains in self.vkdic
                vk.nov = self.nov

        # 2**3 == 8 - number of possible children of the satnoe,
        # put into satnode.chdic
        for val in range(8):
            if val in excl_cvs:
                continue
            sub_vk12dic = {}
            for cvr in tdic:
                if val in cvr:  # touched kn/kv does have outside bit
                    vks = tdic[cvr]
                    for vk in vks:
                        # when added to tnode.vkm, a vk may drop bit for a
                        # specific val. But that bit-drop maybe wrong for
                        # other val. clone it to preserve that vk
                        # in snode.vk12dic
                        sub_vk12dic[vk.kname] = vk.clone()
            # print(f'child-{val}')
            tnode = TNode(sub_vk12dic, snode, val)
            if tnode.vkm.valid:
                TNode.repo[tnode.name] = tnode
                chs[val] = tnode
        # re-make self.bdic, based on updated vkdic (now all 3-bit vks)
        self.make_bdic()  # bdic made here will be used for .next/bestchoice
        return chs  # for making chdic with tnodes
    # enf of def morph()

    def bestchoice(self):
        ''' return: {(kn1,kn2): set([tkn1, tkn2,..]),'bits': bits}
            (kn1,kn2) are the vks (with kn1, kn2 names) sit on same *.bits,
            bits: the 3 bits kn1 and kn2 commonly sit on
            set([tkn1,..]): set of kns/vks that have 1 or 2 bit(s) in bits
            '''
        best_choice = None
        max_tsleng = -1
        max_tcleng = -1
        best_bits = None
        kns = set(self.vkdic.keys())  # candidates-set of kn for besy-key
        while len(kns) > 0:
            kn = kns.pop()
            vk = self.vkdic[kn]
            # sh_sets: {<bit>:<set of kns sharing this bit>,..} for each vk-bit
            sh_sets = {}  # dict keyed by bit, value is a set of kns on the bit
            bits = vk.bits
            for b in bits:
                sh_sets[b] = self.bdic[b].copy()
            # dict.popitem() pops a tuple: (<key>,<value>) from dict
            tsvk = sh_sets.popitem()[1]  # [0] is the bit/key, [1] is the set
            tcvk = tsvk.copy()
            for s in sh_sets.values():
                tsvk = tsvk.intersection(s)
                tcvk = tcvk.union(s)

            chc = (tsvk, tcvk - tsvk)
            kns -= tsvk  # take kns in tsvk out of candidates-set
            ltsvk = len(tsvk)
            if ltsvk < max_tsleng:
                continue
            ltcvk = len(tcvk)
            if not best_choice:
                best_choice = chc
                max_tsleng = ltsvk
                max_tcleng = ltcvk
                best_bits = bits
                # best_bitsum = sum(bits)
            else:
                if best_choice[0] == tsvk:
                    continue
                # see if to replace the best_choice?
                replace = False
                if max_tsleng < ltsvk:
                    replace = True
                elif max_tsleng == ltsvk:
                    if max_tcleng < ltcvk:
                        replace = True
                    elif max_tcleng == ltcvk:
                        if bits > best_bits:
                            replace = True
                if replace:
                    best_choice = chc
                    max_tsleng = ltsvk
                    max_tcleng = ltcvk
                    best_bits = bits
        result = {
            'bestkey': tuple(sorted(list(best_choice[0]))),
            'touched': best_choice[1],
            'bits': best_bits
        }
        return result
    # end of def bestchoice(self):

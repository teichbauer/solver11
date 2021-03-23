from vklause import VKlause
from basics import get_bit, set_bit


class TxEngine:
    """ move base_klause's bits to the top positions as [7,6,5] from 
        [0,1,2,3,4,5,6,7] assign the transfered klause to self.klause.
        While doing this, set up operators so that any klause will be 
        transfered to a new klause compatible to self.klause
        """

    def __init__(self, base_vklause):
        # base_vklause: a vk 2b transfered to the highst bits in nov-bits
        self.start_vklause = base_vklause
        self.txs = {}
        self.setup_tx()

    def setup_tx(self):
        # set of vk.bits
        bits = set(self.start_vklause.bits)
        # target bits
        nov = self.start_vklause.nov
        hi_bits = set(range(nov - 1, nov - 1 - len(bits), -1))

        targets = sorted(list(hi_bits - bits))
        source = sorted(list(bits - hi_bits))

        # transfer for bits to high-bits
        while len(targets) > 0:
            b = source.pop()
            h = targets.pop()
            self.txs[b] = h
            self.txs[h] = b
        # print(str(self.txs))
        L = len(self.txs)
        if L % 2 == 1:
            raise Exception("111")

        # tx the start_vklause to be self.vklause
        self.vklause = self.trans_klause(self.start_vklause)
    # ----- end of def setup_tx(self, hi_bits=None)

    def trans_varray(self, varray):
        assert(self.start_vklause.nov == len(varray)), "!!!!!"
        lst = varray[:]
        for fr, to in self.txs.items():
            lst[to] = varray[fr]
        return lst

    def trans_klause(self, vklause):
        # transfered vk still have the same kname and the same nov
        tdic = {}
        for b, v in vklause.dic.items():
            if b in self.txs:
                tdic[self.txs[b]] = v
            else:
                tdic[b] = v
        if len(tdic) == 0:
            raise Exception("222")
        return VKlause(vklause.kname, tdic, vklause.nov)

    # ----- end of trans_klause

    def trans_vkdic(self, vkdic):
        vdic = {}
        for kn, vk in vkdic.items():
            if kn == self.vklause.kname:
                vdic[kn] = self.vklause.clone()
            else:
                vdic[kn] = self.trans_klause(vk)
        return vdic

    def trans_bdic(self, bdic):
        dic = {}
        for bit, s in bdic.items():
            dic[bit] = {}
            if bit in self.txs:
                dic[self.txs[b]] = bdic[bit]
            else:
                dic[bit] = bdic[b]
        return dic

    def output(self):
        msg = self.name + ': '+str(self.start_vklause.dic) + ', '
        msg += 'txn: ' + str(self.txs) + ', '
        msg += '-'*60
        return msg


if __name__ == '__main__':
    x = 1

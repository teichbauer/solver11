from basics import get_bit, set_bit, set_bits


class VKlause:
    ''' veriable klause - klause with 1, 2 or 3 bits.
        nov is the value-space bit-count, or number-of-variables
        this vk can be a splited version from a origin vk
        the origin field refs to that (3-bits vk)
        '''
    # nov not used - remove it?

    def __init__(self, kname, dic, nov):
        self.kname = kname    # this vk can be a partial one: len(bits) < 3)
        self.dic = dic  # { 7:1, 3: 0, 0: 1}, or {3:0, 1:1} or {3:1}
        self.nov = nov  # number of variables (here: 8) - bits of value space
        # all bits, in descending order
        self.bits = sorted(list(dic.keys()), reverse=True)  # [7,3,0]
        # void bits of the nov-bits
        self.nob = len(self.bits)             # 1, 2 or 3

    def drop_bit(self, bit):
        if len(self.bits) > 1 and bit in self.bits:
            self.bits.remove(bit)
            self.nob -= 1
            self.dic.pop(bit)

    def clone(self, bits2b_dropped=None):
        # bits2b_dropped: list of bits to be dropped.
        # They must be the top-bits
        dic = self.dic.copy()
        new_nov = self.nov
        if bits2b_dropped and len(bits2b_dropped) > 0:
            new_nov = self.nov - len(bits2b_dropped)
            for b in bits2b_dropped:
                # drop off this bit from dic.
                # None: in case b not in dic, it will not cause key-error
                dic.pop(b, None)
        if len(dic):
            return VKlause(self.kname, dic, new_nov)
        else:
            return None

    def clone_tail(self, tailbits, nov):
        d = {}
        for b, v in self.dic.items():
            if b in tail_sat:
                d[b] = v
        if len(d) > 0:
            return VKlause(self.kname, d, nov)
        return None

    def set_value_and_mask(self):
        ''' For the example klause { 7:1,  5:0,     2:1      }
                              BITS:   7  6  5  4  3  2  1  0
            the relevant bits:        *     *        *
                          self.mask:  1  0  1  0  0  1  0  0
            surppose v = 135 bin(v):  1  0  0  0  0  1  1  1
            x = v AND mask =          1  0  0  0  0  1  0  0
            bits of v left(rest->0):  ^     ^        ^
                  self.value(132)  :  1  0  0  0  0  1  0  0
            This method set self.mask
            '''
        mask = 0
        value = 0
        for k, v in self.dic.items():
            mask = mask | (1 << k)
            if v == 1:
                value = value | (1 << k)
        self.value = value
        self.mask = mask

    def hit(self, v):  # hit means here: v let this klause turn False
        if type(v) == type(1):
            if 'mask' not in self.__dict__:
                self.set_value_and_mask()
            fv = self.mask & v
            return not bool(self.value ^ fv)
        elif type(v) == type([]):  # sat-list of [(b,v),...]
            # if self.kname == 'C004':
            #     x = 1
            lst = [(k, v) for k, v in self.dic.items()]
            in_v = True
            for p in lst:
                # one pair/p not in v will make in_v False
                in_v = in_v and (p in v)
            # in_v==True:  every pair in dic is in v
            # in_v==False: at least one p not in v
            return in_v
        elif type(v) == type({}):
            hit_cnt = 0
            for bit, value in self.dic.items():
                if bit in v and v[bit] == value:
                    hit_cnt += 1
            return hit_cnt == self.nob

    def partial_hit_residue(self, sdic, bit_txmap):
        ''' test self is partially hit by sdic (total hit would be
            a bug: it wouldnt be in the candi-tnode).
            For each bit in self.dic:
                transfer bit to v = sh(bit):
                if v is in sdic:
                    if self.dic[bit] != sdic[bit]
                        return None - this vk is not (partially) hit
                    else: dont put this bit/value into td{}
                else(v not in sdic):
                    put into td{}: td[bit] = value
            At the end, if td empty: return None
            if td not empty build a new VKlause from td, return it
            '''
        td = {}
        for bit, value in self.dic.items():
            # v = sh.varray[bit]
            if bit in sdic:
                # one mis-match enough makes it not-hit.
                # if not-hit, tdic(empty or not) not used
                if value != sdic[bit]:
                    return None
            else:
                td[bit] = value
        # getting here means this vk hit in dic-range. And it
        # must be a pratial-hit: outside bit (tdic) must exist
        if len(td) == 0:
            raise Exception(f'vk {self.kname} wrong in this candi-path!')
        else:
            tmpd = {}
            for bit, value in td.items():
                if bit not in bit_txmap:
                    raise Exception("bit-tx-map error")
                tx_bit = bit_txmap[bit]
                if tx_bit in sdic:
                    if td[bit] != sdic[tx_bit]:
                        return None
                else:
                    tmpd[tx_bit] = td[bit]
            if len(tmpd) == 0:
                return None
            return VKlause(self.kname, tmpd, len(bit_txmap))

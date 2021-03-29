from basics import verify_sat, oppo_binary
from restrict import Restrict
from vk12mgr import VK12Manager


class TNode:
    # class-variable repo holds all tnode
    repo = {}   # {<tnode>.name:<tnode-instance>,...}

    def __init__(self, vk12dic, holder_snode, val):
        self.val = val
        self.holder = holder_snode
        self.sh = holder_snode.next_sh
        self.name = f'{self.holder.nov}.{val}'
        self.hsat = holder_snode.sh.get_sats(val)
        self.vkm = VK12Manager(self.sh.ln, vk12dic)

    def check_sat(self, sdic, reverse_sh=False):
        if reverse_sh:
            return verify_sat(self.vkm.vkdic, self.sh.reverse_sdic(sdic))
        return verify_sat(self.vkm.vkdic, sdic)

    def find_path_vk12m(self, ptnode):
        bmap = ptnode.sh.bit_tx_map(self.sh)
        # bit-names(sh) of self.vkm.vk to that of parent-level bit-names(sh)
        ksat = ptnode.sh.reverse_sdic(self.hsat)
        vk12m = self.vkm.clone()  # use a clone, don't touch self.vkm.vks
        # VK12Manager(self.holder.nov)
        # adding all vk-residues from ptnode (vk cut by hsat) to vk12m
        for kn, pvk in ptnode.vkm.vkdic.items():
            vk12 = pvk.partial_hit_residue(ksat, bmap)
            if vk12:
                vk12m.add_vk(vk12)
                if not vk12m.valid:
                    break
        return vk12m

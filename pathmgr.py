from basics import verify_sat
from vk12mgr import VK12Manager
from node12 import Node12


class PathManager:
    sats = []
    limit = 10
    # -------------------------------------------------------------------------
    # Each tnode, if its holder-snode isn't top-level(holder.parent != None)
    #   Each holder-parent(hp) has .chdic:{<v>:<tn>,..}, if hp isn't top-level,
    #   each tn has pthmgr too.
    # Such a tnode has self.pthmgr(instance of PathManager class), with *.dic:
    #   {<vkey>:<vkdic>,...}, where <vkey> is concadinated key(hp isnt top):
    #   <tnode.val>-<tn.val>-<tn.val>... Here last tn is top-level
    #   if hp is top: <tnode.ch-val>-<hp.chdic[v].name>.
    # and <vkdic> is the result of mergings of all tn.vkdic along the way,
    # including self.tnode.vkdic. if the merging is validated.
    # If merging not validated, then this tnode.pthmgr.dic entry
    # will not be created.
    # -------------------------------------------------------------------------

    def __init__(self, tnode, finalize=False):
        # constructed only for tnode, with its holder being non-top level
        self.tnode = tnode
        self.dic = {}
        hp_chdic = tnode.holder.parent.chdic
        if tnode.holder.parent.is_top():  # holder.parent: a top-level snode
            for va, tn in hp_chdic.items():
                if tn.check_sat(tnode.hsat, True):
                    vk12dic = tnode.find_path_vk12dic(tn)
                    if vk12dic:
                        name = f'{self.tnode.val}-{tn.val}'
                        self.dic[name] = vk12dic
        else:  # holder.parent is not top-level snode, its tnodes has pthmgr
            for va, tn in hp_chdic.items():
                sdic = tn.sh.reverse_sdic(tnode.hsat)
                pths = tn.pthmgr.verified_paths(sdic)

                for key, vkd in pths.items():
                    # vkdic = self.extend_vkd(tn.sh, vkd)
                    vkm = self.extend_vkd(tn.sh, vkd)
                    if vkm.valid:
                        if finalize:
                            n12 = Node12(
                                self.tnode.val,
                                self,
                                self.tnode.sh,
                                self.tnode.hsat,
                                vkm
                                # vkdic
                            )
                            if n12.check_done():
                                n12.collect_sat()
                            else:
                                n12.spawn()
                        else:
                            name = f'{self.tnode.val}-{key}'
                            self.dic[name] = vkm

    def add_sat(self, tsat):
        pass

    def verified_paths(self, sdic):
        valid_paths = {}
        for path_name, vkd in self.dic.items():
            if verify_sat(vkd, sdic):
                valid_paths[path_name] = vkd
        return valid_paths

    def extend_vkd(self, src_sh, src_vkd):
        bmap = src_sh.bit_tx_map(self.tnode.sh)
        ksat = src_sh.reverse_sdic(self.tnode.hsat)
        vk12m = VK12Manager(len(bmap))
        for kn, vk in src_vkd.items():
            vk12 = vk.partial_hit_residue(ksat, bmap)
            if vk12:
                vk12m.add_vk(vk12)
        for vk in self.tnode.vkdic.values():
            vk12m.add_vk(vk)
        return vk12m
        # if vk12m.valid:
        #     return vk12m.vkdic
        # return None

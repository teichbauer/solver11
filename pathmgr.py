from basics import verify_sat
from vk12mgr import VK12Manager


class PathManager:
    # -------------------------------------------------------------------------
    # Each tnode, if its holder-snode isn't top-level(holder.parent != None)
    #   Each holder-parent(hp) has .chdic:{<v>:<tn>,..}, if hp isn't top-level,
    #   each tn has pthmgr too.
    # Such a tnode has self.pthmgr(instance of PathManager class), with *.dic:
    #   {<vkey>:<vkdic>,...}, where <vkey> is concadinated key:
    #   <tnode.ch-val>-<hp.chdic[v]-tn.name>-<tn.pthmgr-key>... if hp isnt top.
    #   if hp is top: <tnode.ch-val>-<hp.chdic[v].name>.
    # and <vkdic> is the result of mergings of all tn.vkdic along the way, if
    # the merging is validated. If merging not validated, then this
    # tnode.pthmgr.dic entry will not be created.
    # -------------------------------------------------------------------------

    def __init__(self, tnode):
        # constructed only for tnode, with its holder being non-top level
        self.tnode = tnode
        self.dic = {}
        hp_chdic = tnode.holder.parent.chdic
        if tnode.holder.parent.is_top():  # holder.parent: a top-level snode
            for va, tn in hp_chdic.items():
                if tn.check_sat(tnode.hsat, True):
                    vk12dic = tnode.find_path_vk12dic(tn)
                    if vk12dic:
                        name = f'{tn.name}-{tn.name}'
                        self.dic[name] = vk12dic
        else:  # holder.parent is not top-level snode, its tnodes has pthmgr
            vkd_lst = []
            for va, tn in hp_chdic.items():
                sdic = tn.sh.reverse_sdic(tnode.hsat)
                pths = tn.pthmgr.verified_paths(sdic)

                for key, vkd in pths.items():
                    vkd = self.extend_vkd(tn.sh, vkd)
                    if vkd:
                        name = f'{self.tnode.name}-{key}'
                        self.dic[name] vkd

    def verified_paths(self, sdic):
        valid_paths = {}
        for path_name, vkd in self.dic.items():
            if verify_sat(vkd, sdic):
                valid_paths[path_name] = vkd
        return valid_paths

    def extend_vkd(self, src_sh, src_vkd):
        bmap = src_sh.bit_tx_map(self.tnode.sh)
        ksat = src_sh.reverse_sdic(self.tnode.hsat)
        vk12m = VK12Manager(self.tnode.holder.nov)
        for kn, vk in src_vkd.items():
            vk12 = vk.partial_hit_residue(ksat, bmap)
            if vk12:
                vk12m.add_vk(vk12)
        if vk12m.valid:
            return vk12m.vkdic
        return None

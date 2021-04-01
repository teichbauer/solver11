from basics import verify_sat, display_vkdic
from vk12mgr import VK12Manager
from node12 import Node12


class PathManager:
    sats = []
    limit = 10
    # debug = False
    debug = True
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

    def __init__(self, tnode, final=False):  # snode.done==final
        # constructed only for tnode, with its holder being non-top level
        self.tnode = tnode
        print(f'making pth-mgr for {tnode.name}')
        self.dic = {}
        hp_chdic = tnode.holder.parent.chdic
        if tnode.holder.parent.is_top():  # holder.parent: a top-level snode
            for va, tn in hp_chdic.items():
                if tn.check_sat(tnode.hsat, True):
                    vk12m = tnode.find_path_vk12m(tn)
                    if vk12m.valid:
                        names = [tn.name]
                        if final:
                            self.finalize(vk12m, names)
                        else:
                            names.insert(0, tnode.name)
                            self.dic[tuple(names)] = vk12m
        else:  # holder.parent is not top-level snode, its tnodes has pthmgr
            for va, tn in hp_chdic.items():
                sdic = tn.sh.reverse_sdic(tnode.hsat)
                pths = tn.pthmgr.verified_paths(sdic)
                ks = list(pths.keys())
                if self.debug:
                    print(f'{len(ks)} path-keys: {ks}')
                x = 1
                for key, vkm in pths.items():
                    # print(f'proccessing {key}')
                    msg = f'{tnode.name}-{key}'
                    if msg == "54.1-('57.2', '60.1')":
                        debug = 1
                    elif msg == "54.0-('57.3', '60.6')":
                        debug = 1
                    if self.debug:
                        print(f'extend-vkm for {msg}')
                        display_vkdic(tnode.vkm.vkdic,
                                      f'vkdic of tnode: {tnode.name}')
                        display_vkdic(vkm.vkdic, 'adding vkdic')
                    vk12m = self.extend_vkm(tn.sh, vkm)
                    path_name = list(key)
                    if vk12m.valid:
                        if final:
                            self.finalize(vk12m, path_name)
                        else:
                            path_name.insert(0, tnode.name)
                            self.dic[tuple(path_name)] = vk12m

    def finalize(self, vkm, pathname):
        n12 = Node12(
            self.tnode.val,
            self,
            self.tnode.sh.clone(),
            self.tnode.hsat,
            vkm)
        n12.path_name = pathname
        if n12.done:
            n12.collect_sat()
        else:
            n12.spawn()

    def verified_paths(self, sdic):
        valid_paths = {}
        for path_name, vkm in self.dic.items():
            if verify_sat(vkm.vkdic, sdic):
                valid_paths[path_name] = vkm
        return valid_paths

    def extend_vkm(self, src_sh, src_vkm):
        bmap = src_sh.bit_tx_map(self.tnode.sh)
        ksat = src_sh.reverse_sdic(self.tnode.hsat)
        vk12m = self.tnode.vkm.clone()
        for kn, vk in src_vkm.vkdic.items():
            vk12 = vk.partial_hit_residue(ksat, bmap)
            if vk12:
                vk12m.add_vk(vk12)
                if not vk12m.valid:
                    break
        return vk12m

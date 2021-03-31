import sys
import time
from basics import get_sdic, ordered_dic_string, verify_sat
from satholder import SatHolder
from satnode import SatNode
from vkmgr import VKManager
from vklause import VKlause


def make_vkdic(kdic, nov):
    vkdic = {}
    for kn, klause in kdic.items():
        vkdic[kn] = VKlause(kn, klause, nov)
    return vkdic


def make_vkm(cnf_fname):
    vkdic, nov = get_vkdic_from_cfg(cnf_fname)
    return VKManager(vkdic, nov, True)


def process(cnfname):
    vkm = make_vkm(cnfname)
    satslots = list(range(vkm.nov))
    sh = SatHolder(satslots)
    SatNode.maxnov = sh.ln

    sn = SatNode(None, sh, vkm)
    while not sn.done:
        print(f'spawning at nov = {sn.nov}')
        sn = sn.spawn()
    return sn.solve()


def get_vkdic_from_cfg(cfgfile):
    sdic = get_sdic(cfgfile)

    vkdic = make_vkdic(sdic['kdic'], sdic['nov'])
    return vkdic, sdic['nov']


def work(configfilename, verify=True):
    start_time = time.time()
    sats = process(configfilename)
    now_time = time.time()
    time_used = now_time - start_time
    ln = len(sats)
    print(f'there are {ln} sats:')

    vkdic, dummy = get_vkdic_from_cfg(configfilename)

    for ind, sat in enumerate(sats):
        msg = ordered_dic_string(sat)
        m = f'{ind+1}: {msg}'
        if verify:
            verified = verify_sat(vkdic, sat)
            m += f', verified: {verified}'
        print(m)
    print(f'Time used: {time_used}')


if __name__ == '__main__':
    global FINAL
    # configfilename = 'cfg100-450.json'
    configfilename = 'cfg60-266.json'
    # configfilename = 'cfg60-262.json'
    # configfilename = 'config1.json'
    # configfilename = 'cfg12-45.json'
    # configfilename = 'cfg12-55.json'

    if len(sys.argv) > 1:
        configfilename = sys.argv[1].strip()

    work(configfilename)

    x = 1

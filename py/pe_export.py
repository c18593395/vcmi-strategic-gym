# 解析 PE 导出表: 给定 dll 和导出名, 输出 func RVA 与 objdump 用的 VMA
# 用法: python pe_export.py <dll路径> <mangled_name> [更多名字...]
import struct, sys

def main():
    path = sys.argv[1]
    targets = sys.argv[2:]
    d = open(path, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    assert d[pe:pe+4] == b'PE\x00\x00', 'not PE'
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    ib = struct.unpack_from('<Q', d, opt + 24)[0]  # ImageBase (PE32+)
    dd = opt + (112 if magic == 0x20b else 96)
    erva, sz = struct.unpack_from('<II', d, dd)
    secs = []
    sec0 = opt + optsz
    for i in range(nsec):
        nm, vz, va, rs, ro = struct.unpack('<8sIIII', d[sec0 + i*40:][:24])
        secs.append((vz, va, rs, ro))
    def r2o(r):
        for vz, va, rs, ro in secs:
            if va <= r < va + max(vz, rs):
                return ro + (r - va)
        return None
    eo = r2o(erva)
    assert eo, 'erva not in any section'
    funcs_rva = struct.unpack_from('<I', d, eo + 28)[0]
    names_rva = struct.unpack_from('<I', d, eo + 32)[0]
    ords_rva = struct.unpack_from('<I', d, eo + 36)[0]
    nnames = struct.unpack_from('<I', d, eo + 24)[0]
    nfuncs = struct.unpack_from('<I', d, eo + 20)[0]
    name_rva = struct.unpack_from('<I', d, eo + 12)[0]
    print(f'erva={erva:#x} file_off={eo:#x} magic={magic:#x} nfuncs={nfuncs} nnames={nnames} name_rva={name_rva:#x}')
    fo, no_, oo = r2o(funcs_rva), r2o(names_rva), r2o(ords_rva)
    for t in targets:
        tb = t.encode() + b'\x00'
        found = None
        for i in range(nnames):
            nrva = struct.unpack_from('<I', d, no_ + i*4)[0]
            o = r2o(nrva)
            if o and d[o:o + len(tb)] == tb:
                found = i
                break
        if found is None:
            print(f'{t}: NOT FOUND')
            continue
        frva = struct.unpack_from('<I', d, fo + found*4)[0]
        ordn = struct.unpack_from('<H', d, oo + found*2)[0]
        print(f'{t}: ordinal={ordn} rva={frva:#x} objdump_vma={ib + frva:#x}')

main()

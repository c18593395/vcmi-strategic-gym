"""
P8-C 阶段4: 171KB StartGame 全状态解析器 (最小 CGameState 解析)
目标: 提取我方英雄 OI + 起始坐标, 使 MoveHero 闭环.

wire 格式 (C++ BinarySerializer 权威, 逐项核对):
- 整数 si32/ui32/int64 = LVarInt; uint8/int8/bool/uint8底层枚举 = 1B raw
- 容器 count = LVarInt
- string = LVarInt 长度 + utf8 bytes; 长度<0 = 全局去重ID (负数)
- shared_ptr/unique_ptr 非空 = isNull(1B=0) + pid(LVarInt) + typeID(LVarInt)
  已序列化对象再引用 = isNull(0) + pid(LVarInt) 仅两字段
  空指针 = isNull(1B=1)
- unregistered 类型 typeID=0 → 数据内联展开

CRITICAL: decode_lvarint(buf,pos) 返回 (value, new_pos), 不是 (value, byte_count)
锚点断言: StartInfo mode=0/difficulty=1/playerInfos=2, CMap width=36/height=36, day=1
"""
import sys, struct, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.serialization import decode_lvarint

BIN = os.path.join(os.environ.get('LOCALAPPDATA','C:\\Users\\Administrator\\AppData\\Local'),'Temp','p8c_startgame.bin')
B = open(BIN,'rb').read()
L = len(B)
ptr_seen = set()
str_table = []
diag = []

def r_lvarint(p):
    """返回 (value, new_pos)"""
    return decode_lvarint(B, p)
def r_u8(p):
    return B[p], p+1
def r_bool(p):
    return B[p]!=0, p+1
def r_u16raw(p):
    return struct.unpack('<H', B[p:p+2])[0], p+2

def r_str(p):
    ln, p = r_lvarint(p)
    if ln < 0:
        return str_table[-ln-1], p
    s = B[p:p+ln].decode('utf-8','replace'); p += ln
    str_table.append(s); return s, p

def r_ptr(p, parse_fn=None):
    """返回 (obj, pid, tid, is_null, was_ref, new_p)"""
    isnull = B[p]; p += 1
    if isnull:
        return None, 0, 0, True, False, p
    pid, p = r_lvarint(p)
    if pid in ptr_seen:
        return ('REF',pid), pid, 0, False, True, p
    tid, p = r_lvarint(p)
    ptr_seen.add(pid)
    if parse_fn is None:
        return None, pid, tid, False, False, p
    obj, p = parse_fn(p)
    return obj, pid, tid, False, False, p

def r_int3(p):
    x,p=r_lvarint(p); y,p=r_lvarint(p); z,p=r_lvarint(p)
    return (x,y,z),p

# ===== CMapGenOptions (version 905: MORE_MAP_LAYERS + TIMER_MOVEMENT_POINTS) =====
def parse_cmapgenoptions(p):
    w,p=r_lvarint(p); h,p=r_lvarint(p); lv,p=r_lvarint(p)
    diag.append(('CMapGenOptions', dict(width=w,height=h,levels=lv)))
    for _ in range(4): p=r_lvarint(p)[1]
    p=r_lvarint(p)[1]; p=r_lvarint(p)[1]
    pc,p=r_lvarint(p)
    for _ in range(pc):
        p=r_lvarint(p)[1]
        for _ in range(5): p=r_lvarint(p)[1]
    p=r_str(p)[1]
    rc,p=r_lvarint(p)
    for _ in range(rc): p=r_lvarint(p)[1]
    return p

# ===== StartInfo inner =====
def parse_startinfo(p):
    mode,p=r_lvarint(p); diff,p=r_u8(p)
    diag.append(('StartInfo.mode',mode)); diag.append(('StartInfo.difficulty',diff))
    cnt,p=r_lvarint(p)
    diag.append(('StartInfo.playerInfos.count',cnt))
    players=[]
    for _ in range(cnt):
        key,p=r_lvarint(p)
        castle,p=r_lvarint(p); hero,p=r_lvarint(p); hport,p=r_lvarint(p)
        hname,p=r_str(p); bonus,p=r_lvarint(p); color,p=r_lvarint(p)
        for _ in range(9): p=r_lvarint(p)[1]   # handicap TResources
        name,p=r_str(p)
        cp,p=r_lvarint(p)
        for _ in range(cp): p=r_lvarint(p)[1]
        co,p=r_bool(p)
        players.append(dict(key=key,castle=castle,hero=hero,color=color,name=name,compOnly=co))
    diag.append(('StartInfo.players',players))
    p=r_lvarint(p)[1]      # startTime
    p=r_str(p)[1]          # fileURI
    for _ in range(4): p=r_lvarint(p)[1]   # simturnsInfo
    for _ in range(2): p=r_bool(p)[1]
    for _ in range(4): p=r_lvarint(p)[1]   # turnTimerInfo
    for _ in range(6): p=r_bool(p)[1]
    for _ in range(2): p=r_bool(p)[1]      # extraOptionsInfo
    mapname,p=r_str(p)
    diag.append(('StartInfo.mapname',mapname))
    mgo,mgo_pid,mgo_tid,mgo_null,mgo_ref,p = r_ptr(p, parse_cmapgenoptions)
    diag.append(('StartInfo.mapGenOptions','null' if mgo_null else ('ref' if mgo_ref else 'present(tid=%d)'%mgo_tid)))
    cs,cs_pid,cs_tid,cs_null,cs_ref,p = r_ptr(p, None)
    diag.append(('StartInfo.campState','null' if cs_null else 'present'))
    return p

# ===== CMapHeader =====
def parse_cmapheader(p):
    tc,p=r_lvarint(p)
    for _ in range(tc):
        p=r_str(p)[1]
        p=r_str(p)[1]; p=r_str(p)[1]; p=r_str(p)[1]
    diag.append(('CMapHeader.texts.count',tc))
    ver,p=r_u8(p)
    diag.append(('CMapHeader.version',ver))
    mc,p=r_lvarint(p)
    for _ in range(mc):
        p=r_str(p)[1]; p=r_lvarint(p)[1]
    for _ in range(5):
        p=r_metastring(p)
    p=r_lvarint(p)[1]      # creationDateTime
    w,p=r_lvarint(p); h,p=r_lvarint(p)
    diag.append(('CMap.width',w)); diag.append(('CMap.height',h))
    ml,p=r_lvarint(p)
    mvals=[]
    for _ in range(ml):
        v,p=r_lvarint(p); mvals.append(v)
    diag.append(('CMap.mapLayers',mvals))
    p=r_lvarint(p)[1]
    p=r_u8(p)[1]
    p=r_bool(p)[1]
    p=r_bool(p)[1]
    pc,p=r_lvarint(p); diag.append(('CMap.players.count',pc))
    for _ in range(pc):
        p=r_bool(p)[1]; p=r_lvarint(p)[1]; p=r_bool(p)[1]; p=r_bool(p)[1]; p=r_lvarint(p)[1]
        afc,p=r_lvarint(p)
        for _ in range(afc): p=r_lvarint(p)[1]
        p=r_bool(p)[1]; p=r_lvarint(p)[1]; p=r_str(p)[1]
        hnc,p=r_lvarint(p)
        for _ in range(hnc):
            p=r_lvarint(p)[1]; p=r_str(p)[1]
        p=r_bool(p)[1]; p=r_bool(p)[1]
        p=r_int3(p)[1]; p=r_lvarint(p)[1]; p=r_str(p)[1]
    p=r_u8(p)[1]
    ahc,p=r_lvarint(p)
    for _ in range(ahc): p=r_lvarint(p)[1]
    rcc,p=r_lvarint(p)
    for _ in range(rcc): p=r_lvarint(p)[1]
    p=r_metastring(p)
    p=r_lvarint(p)[1]
    p=r_metastring(p)
    p=r_lvarint(p)[1]
    dhc,p=r_lvarint(p)
    for _ in range(dhc):
        p=r_lvarint(p)[1]; p=r_lvarint(p)[1]; p=r_str(p)[1]
        pcc,p=r_lvarint(p)
        for _ in range(pcc): p=r_lvarint(p)[1]
    diag.append(('CMap.disposedHeroes.count',dhc))
    return p

# ===== CMap inner =====
def parse_cmap(p):
    p = parse_cmapheader(p)
    tec,p=r_lvarint(p); diag.append(('CMap.triggeredEvents.count',tec))
    p=r_str(p)[1]
    for _ in range(3):
        sc,p=r_lvarint(p)
        for _ in range(sc): p=r_lvarint(p)[1]
    ec,p=r_lvarint(p); diag.append(('CMap.events.count',ec))
    p=r_int3(p)[1]
    ac,p=r_lvarint(p); diag.append(('CMap.artInstances.count',ac))
    for _ in range(ac):
        p=r_ptr(p, None)[5]
    hpc,p=r_lvarint(p); diag.append(('CMap.heroesPool.count',hpc))
    for _ in range(hpc):
        p=r_ptr(p, None)[5]
    p=r_lvarint(p)[1]
    tz,p=r_lvarint(p); tx,p=r_lvarint(p); ty,p=r_lvarint(p)
    diag.append(('CMap.terrain.dims',(tz,tx,ty)))
    tcount=tz*tx*ty
    for _ in range(tcount):
        p=r_lvarint(p)[1]; p=r_u8(p)[1]
        p=r_lvarint(p)[1]; p=r_u8(p)[1]
        p=r_lvarint(p)[1]; p=r_u8(p)[1]; p=r_u8(p)[1]
        vo,p=r_lvarint(p)
        for _ in range(vo): p=r_lvarint(p)[1]
        bo,p=r_lvarint(p)
        for _ in range(bo): p=r_lvarint(p)[1]
    diag.append(('CMap.terrain.parsed',tcount))
    p=r_lvarint(p)[1]
    gz,p=r_lvarint(p); gx,p=r_lvarint(p); gy,p=r_lvarint(p)
    gcount=gz*gx*gy
    for _ in range(gcount):
        p=r_lvarint(p)[1]; p=r_lvarint(p)[1]; p=r_lvarint(p)[1]
    diag.append(('CMap.guarding.parsed',gcount))
    oc,p=r_lvarint(p); diag.append(('CMap.objects.count',oc))
    for _ in range(oc):
        p=r_ptr(p, None)[5]
    hom,p=r_lvarint(p)
    heros=[]
    for _ in range(hom):
        v,p=r_lvarint(p); heros.append(v)
    diag.append(('CMap.heroesOnMap',heros))
    return p, {'heroesOnMap':heros, 'objectsCount':oc}

# ===== CGameState inner =====
def parse_gamestate(p):
    p=r_ptr(p, None)[5]
    p=r_ptr(p, None)[5]
    ac,p=r_lvarint(p)
    act=[]
    for _ in range(ac):
        v,p=r_lvarint(p); act.append(v)
    diag.append(('CGameState.actingPlayers',act))
    day,p=r_lvarint(p)
    diag.append(('CGameState.day',day))
    cm,cm_pid,cm_tid,cm_null,cm_ref,p = r_ptr(p, None)
    result={}
    if not cm_null and not cm_ref:
        p, result = parse_cmap(p)
    return p, result

# ===== MetaString (5 容器) =====
def r_metastring(p):
    c,p=r_lvarint(p)
    for _ in range(c): p=r_str(p)[1]
    c,p=r_lvarint(p)
    for _ in range(c): p=r_u8(p)[1]; p=r_lvarint(p)[1]
    c,p=r_lvarint(p)
    for _ in range(c): p=r_str(p)[1]
    c,p=r_lvarint(p); p+=c
    c,p=r_lvarint(p)
    for _ in range(c): p=r_lvarint(p)[1]
    return p

def main():
    print('总长 =', L, 'first16 =', B[:16].hex(' '))
    # 外层帧 b[0:4]: isNull(1B)+pid(LVarInt)+tid(LVarInt)
    p = 0
    isnull = B[p]; p += 1
    p = r_lvarint(p)[1]     # pid
    p = r_lvarint(p)[1]     # tid
    print('外层帧结束 @%d'%p)
    si,_sp,_st,snull,sref,p = r_ptr(p, parse_startinfo)
    print('startInfo: null=%s ref=%s, @pos=%d'%(snull,sref,p))
    for d in diag:
        print('  ', d)
    diag.clear()
    print('解析 StartInfo 后 pos=%d'%p)
    gs,_gp,_gt,gnull,gref,p = r_ptr(p, parse_gamestate)
    print('CGameState: null=%s ref=%s, @pos=%d'%(gnull,gref,p))
    for d in diag:
        print('  ', d)
    out = {'heroesOnMap': gs.get('heroesOnMap',[]), 'objectsCount': gs.get('objectsCount',0)}
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'p8c_hero_extract.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print('\n=== 提取结果 ===')
    print('heroesOnMap =', out['heroesOnMap'])
    print('objectsCount =', out['objectsCount'])

if __name__=='__main__':
    main()

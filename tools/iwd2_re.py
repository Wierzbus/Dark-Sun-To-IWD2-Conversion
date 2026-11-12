"""Pomocnicze funkcje analizy IWD2.exe (GOG 2.01, sha256 18e01d21...): napisy, odwolania, deasemblacja przez objdump.
Ustaw IWD2_EXE na sciezke do pliku. Tylko odczyt."""
import re, struct, subprocess
import os
D=open(os.environ.get('IWD2_EXE','IWD2.exe'),'rb').read()
BASE=0x400000
TEXT=(0x1000,0x1000+0x4458f1)
def va(off): return off+BASE
def off(v): return v-BASE
def find_str(s, ci=True):
    pat=re.escape(s.encode()); fl=re.I if ci else 0
    return [va(m.start()) for m in re.finditer(pat+b'\0',D,fl)]
def xrefs(v):
    b=struct.pack('<I',v); out=[]; i=D.find(b,TEXT[0])
    while 0<=i<TEXT[1]:
        out.append(va(i)); i=D.find(b,i+1)
    return out
def dis(start, n=60):
    r=subprocess.run(['objdump','-d','-M','intel','--no-show-raw-insn',f'--start-address={start:#x}',f'--stop-address={start+n*7:#x}',os.environ.get('IWD2_EXE','IWD2.exe')],capture_output=True,text=True).stdout
    return '\n'.join(l for l in r.splitlines() if re.match(r'\s+[0-9a-f]+:',l))
def cstr(v):
    o=off(v); e=D.find(b'\0',o); return D[o:e].decode('latin-1')

def table_globals():
    """push imm32(nazwa) ; mov ecx, imm32(obiekt) ; call LOAD2DA -> {nazwa: obiekt}"""
    out={}
    for m in re.finditer(rb'\x68(....)\xb9(....)\xe8(....)', D[TEXT[0]:TEXT[1]], re.S):
        s,obj,rel=struct.unpack('<IIi',m.group(1)+m.group(2)+m.group(3))
        call=va(TEXT[0]+m.start()+10)+5+rel
        if call!=0x7fcc88 or not (0x847000<=s<0x8c6000): continue
        out[cstr(s)]=obj
    return out

FUNC_STARTS=None
def func_start(v):
    """cofnij do poczatku funkcji: po bajtach wypelnienia CC/90 przed 'push ebp|push reg|sub esp'"""
    o=off(v)
    while o>TEXT[0]:
        if D[o-1] in (0xCC,0x90) and D[o] not in (0xCC,0x90) and (D[o-2] in (0xCC,0x90,0xC3) or D[o-1]==0xCC):
            return va(o)
        o-=1
    return None

def refs_range(lo, hi):
    """wszystkie 4-bajtowe odwolania w .text do adresow w [lo,hi)"""
    out=[]
    t=D[TEXT[0]:TEXT[1]]
    for i in range(len(t)-3):
        v=t[i]|t[i+1]<<8|t[i+2]<<16|t[i+3]<<24
        if lo<=v<hi: out.append((va(TEXT[0]+i),v))
    return out

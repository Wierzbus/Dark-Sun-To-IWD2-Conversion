import sys,re
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), 'dane')); from klasy_prestizowe_t52 import P, SK
R='/home/claude/Dark-Sun-To-IWD2-Conversion'
M=R+'/mod/darksun_rasy'
K0=52
BAB={'BAATFGT':('full','pełna'),'BAATNFG':('3/4','3/4'),'BAATMAG':('1/2','1/2')}
SV={'SAVEWAR':(['Fortitude'],['Wytrwałość']),'SAVEWIZ':(['Will'],['Wola']),'SAVEROG':(['Reflex'],['Refleks']),'SAVEPRS':(['Fortitude','Will'],['Wytrwałość','Wola']),
    'SAVEMONK':(['Fortitude','Reflex','Will'],['Wytrwałość','Refleks','Wola']),'SAVEBRD':(['Reflex','Will'],['Refleks','Wola']),'SAVEDSFR':(['Fortitude','Reflex'],['Wytrwałość','Refleks'])}
for i,p in enumerate(P):
    p['k']=K0+i; p['t']=901+10*i
# --- CLAB
cl=open(R+'/tools/iwd2_clab.py').read()
if 'CLABDS52' not in cl:
    add='    # --- test52: klasy prestizowe Dark Sun 3.5e i Forgotten Realms Campaign Setting ---\n'
    for p in P:
        wp=', '.join(f'({l}, "{("FA_%fa_"+str(p["t"]+3)+"%") if a=="FA" else a}")' for l,a in p['clab'])
        add+=f'    "CLABDS{p["k"]}": [{wp}],  # {p["n"]}\n'
    cl=cl.replace('\n}\n\n\ndef clab', '\n'+add+'}\n\n\ndef clab',1)
    open(R+'/tools/iwd2_clab.py','w').write(cl)
# --- DSKLPROG
f=M+'/darksun_rasy/2da/DSKLPROG.2DA'; s=open(f,newline='').read()
for p in P:
    if not re.search(r'(?m)^'+p['n']+r'\s',s):
        s=s.rstrip('\n')+'\n'+f"{p['n']:<16}{p['hp']:<10}{p['bab']:<10}{p['sv']:<10}*         *"+'\n'
open(f,'w',newline='').write(s)
# --- DSPREST
f=M+'/darksun_rasy/2da/DSPREST.2DA'; s=open(f,newline='').read()
for p in P:
    if re.search(r'(?m)^'+p['n']+r'\s',s): continue
    lv,bab,cls,cll,mx,race,f1,f2,f3,s1,r1,s2,r2,arc,spc=p['pre']
    s1=SK[s1] if s1 else 0; s2=SK[s2] if s2 else 0
    s=s.rstrip('\n')+'\n'+f"{p['n']:<16}{lv:<7}{bab:<5}{cls:<7}{cll:<13}{'*':<12}{mx:<11}{race:<6}{f1:<7}{f2:<7}{f3:<7}{s1:<8}{r1:<7}{s2:<8}{r2:<7}{arc:<3}{spc}"+'\n'
open(f,'w',newline='').write(s)
# --- DSKLASY: ataki z zaskoczenia
f=M+'/darksun_rasy/2da/DSKLASY.2DA'; d=open(f,newline='').read(); nl='\r\n' if '\r\n' in d else '\n'; L=d.split(nl)
for p in P:
    if p['sneak'] and p['n'] not in L[2]:
        L[2]=L[2].rstrip()+'  '+p['n']
        for j in range(3,len(L)):
            if L[j].strip(): L[j]=L[j].rstrip()+'  '+(str(p['sneak']) if L[j].split()[0]=='SNEAK_ATTACK' else '0')
open(f,'w',newline='').write(nl.join(L))
# --- tra
def help_txt(p,pl):
    b=BAB[p['bab']][1 if pl else 0]; sv=', '.join(SV[p['sv']][1 if pl else 0]); pts=p['sp']*2
    src='Dark Sun 3.5e' if p['src']=='DS' else 'Forgotten Realms Campaign Setting'
    if pl:
        t=f"{p['pl'][1].upper()} (klasa prestiżowa, {src}): {p['dpl']}\n\nWymagania: {p['req_pl']}\n\nKość wytrzymałości: {p['kw'].replace('d','k')}. Bazowa premia do ataku: {b}. Dobre rzuty obronne: {sv}. Punkty umiejętności: {pts} na poziom."
        if p.get('impl_pl'): t+=f"\n\nZdolności: {p['impl_pl']}"
        fa=f"{p['pl'][1]}: {p['fpl']} – tylko opis."
    else:
        t=f"{p['en'][1].upper()} (prestige class, {src}): {p['den']}\n\nRequirements: {p['req_en']}\n\nHit Die: {p['kw']}. Base attack bonus: {b}. Good saving throws: {sv}. Skill points: {pts} per level."
        if p.get('impl_en'): t+=f"\n\nAbilities: {p['impl_en']}"
        fa=f"{p['en'][1]}: {p['fen']} - description only."
    return t,fa
for fn,enc,pl in (('english.tra','cp1252',0),('polish.tra','cp1250',1)):
    f=M+'/darksun_rasy/tra/'+fn; s=open(f,'rb').read().decode(enc); nl='\r\n' if '\r\n' in s else '\n'
    if '@901 =' in s: continue
    add=nl+('// test52: klasy prestizowe DS 3.5e i FRCS')
    for p in P:
        h,fa=help_txt(p,pl); nm=p['pl'] if pl else p['en']
        for k,v in ((0,nm[0]),(1,nm[1]),(2,h),(3,fa)):
            add+=nl+f"@{p['t']+k} = ~{v.replace(chr(10),nl)}~"
    s=s.rstrip('\r\n')+add+nl
    s=s.replace('û','u') if enc=='cp1250' else s
    open(f,'wb').write(s.encode(enc))
# --- tp2
f=M+'/setup-darksun_rasy.tp2'; s=open(f,encoding='latin1').read()
def ins(a,b):
    global s
    assert s.count(a)==1,(a[:70],s.count(a)); s=s.replace(a,a+b)
if 'DUNE_TRADER' not in s:
    s=s.replace('VERSION ~test51-2026-11-18~','VERSION ~test52-2026-11-18~')
    ins('    51, 1, SZ_LYCANTHROPE , CLABDS51, 34 => 791\n','    // test52: klasy prestizowe Dark Sun 3.5e (Athas.org) i Forgotten Realms Campaign Setting\n'+''.join(f"    {p['k']}, 1, {p['n']:<15}, CLABDS{p['k']}, {p['k']+1:02X} => {p['t']}\n" for p in P))
    s=s.replace('  OUTER_SET ds_n_kitow = 52',f'  OUTER_SET ds_n_kitow = {K0+len(P)}')
    # hidden flag: wpisy >= 32 ukryte - klasy prestizowe 52+ musza byc widoczne!
    a='            WRITE_LONG o (k_0 >= 32 ? 2 : 1)    // test45: 2 = ukryta (klasy potworow)'
    assert a in s
    s=s.replace(a,f'            WRITE_LONG o (((k_0 >= 32) AND (k_0 < {K0})) ? 2 : 1)    // test45: 2 = ukryta (klasy potworow, NPC, szablony 32..{K0-1}); test52: klasy prestizowe {K0}+ widoczne')
    ins('  OUTER_SET $ds_str(~793~) = RESOLVE_STR_REF(@793)\n','  // test52\n'+''.join(f"  OUTER_SET $ds_str(~{p['t']+j}~) = RESOLVE_STR_REF(@{p['t']+j})\n" for p in P for j in range(3)))
    ins('  APPEND ~ALIGNMNT.2DA~ ~SZ_LYCANTHROPE\t1\t1\t1\t1\t1\t1\t1\t1\t1~ UNLESS ~SZ_LYCANTHROPE~\n',''.join(f"  APPEND ~ALIGNMNT.2DA~ ~{p['n']}\t{p['al']}~ UNLESS ~{p['n']}~\n" for p in P))
    ins('        LPF ds_wiersz_kitu STR_VAR wiersz = ~SZ_LYCANTHROPE~ wzor = ~BARBARIAN~ END\n',''.join(f"        LPF ds_wiersz_kitu STR_VAR wiersz = ~{p['n']}~ wzor = ~BARBARIAN~ END\n" for p in P))
    fc='    // test52: klasy prestizowe - premiowe atuty (wiersz = poziom - 1)\n'
    for p in P:
        fc+=f"    LPF ds_kolumna_zera STR_VAR kol = ~{p['n']}~ wzor = ~BARBARIAN~ END\n"+''.join(f"    LPF ds_kol_wart INT_VAR wiersz = {r} wart = 1 END\n" for r in p['feat'])
    ins('    LPF ds_kolumna_zera STR_VAR kol = ~SZ_LYCANTHROPE~ wzor = ~BARBARIAN~ END\n',fc)
    sp='    // test52: klasy prestizowe (wartosc = punkty / 2)\n'+''.join(f"    LPF ds_kolumna_kitu STR_VAR kol = ~{p['n']}~ wzor = ~BBN~ END\n    LPF ds_kol_wart INT_VAR wiersz = 0 wart = {p['sp']} END\n" for p in P)
    ins('    LPF ds_kolumna_kitu STR_VAR kol = ~SZ_LYCANTHROPE~ wzor = ~BBN~ END\n    LPF ds_kol_wart INT_VAR wiersz = 0 wart = 1 END\n',sp)
    sc='    // test52: klasy prestizowe - umiejetnosci klasy, z ktorej zwykle sie wchodzi\n'+''.join(f"    LPF ds_kolumna_kitu STR_VAR kol = ~{p['n']}~ wzor = ~{p['sk']}~ END\n" for p in P)
    ins("    LPF ds_kolumna_kitu STR_VAR kol = ~WARPRIEST~     wzor = ~CLR~ END\n",sc)
    ins('  OUTER_SET fa_794 = RESOLVE_STR_REF(@794)\n',''.join(f"  OUTER_SET fa_{p['t']+3} = RESOLVE_STR_REF(@{p['t']+3})\n" for p in P))
    a='~CLABDS50~ ~CLABDS51~ BEGIN'
    assert s.count(a)==1
    s=s.replace(a,'~CLABDS50~ ~CLABDS51~\n                       '+' '.join(f"~CLABDS{p['k']}~" for p in P)+' BEGIN')
    ins('       ~darksun_rasy/spl/DSMNDV.SPL~  ~override~\n','       ~darksun_rasy/spl/DSSDEF.SPL~  ~override~   // test52: +1 do rzutow obronnych (Sacred/Shadow Defense)\n')
open(f,'w',encoding='latin1').write(s)
# --- SPL
f=R+'/tools/iwd2_spl.py'; s=open(f).read()
if 'DSSDEF' not in s:
    a='    "DSSWWIL": [efekt(35, p1=2, p2=0)],'
    s=s.replace(a,a+'\n    # test52 Sacred / Shadow Defense: +1 do Wytrwalosci, Refleksu i Woli (opcode 33/34/35)\n    "DSSDEF": [efekt(33, p1=1, p2=0), efekt(34, p1=1, p2=0), efekt(35, p1=1, p2=0)],',1)
    open(f,'w').write(s)
print('ok', K0+len(P))

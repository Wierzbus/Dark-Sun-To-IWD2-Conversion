"""test47: klasy NPC (adept/ekspert/wojownik NPC) i klasy szablonow -> nowy DSPOTWOR.2DA.

Wejscie: stary DSPOTWOR.2DA (test46, klasy potworow), /tmp/dnd/cre_ids.json, cre_iwd2.json, cre_czary.json.
Wyjscie: DSPOTWOR.2DA z kolumnami KIT SZAB L1..L11 HP STR INT WIS DEX CON CHA CR
  KIT  - ukryta podklasa klasy podstawowej (MON_*, NPC_*) albo * (klasy CRE bez podklasy)
  SZAB - ukryta podklasa szablonu na klasie 1 albo *
  L1..L11 - poziomy klas (BAR..WIZ) po zmianie; suma = dotychczasowy poziom CRE
"""
import json, re, math, sys
REPO = '/tmp/dnd/DSPOTWOR_t46.2DA'   # test46: kolumny KIT HP cechy CR
C = {c['res']: c for c in json.load(open('/tmp/dnd/cre_ids.json'))}
A = {c['res'].upper(): c for c in json.load(open('/tmp/dnd/cre_iwd2.json'))}
SP = json.load(open('/tmp/dnd/cre_czary.json'))

stary = {}
for l in open(REPO).read().split('\n')[3:]:
    p = l.split()
    if len(p) == 10: stary[p[0].upper()] = p[1:]

KIT_KL = {'NPC_WARRIOR': 5, 'NPC_EXPERT': 9, 'NPC_ADEPT': 3}
KOSC_KL = [6.5, 3.5, 4.5, 4.5, 5.5, 4.5, 5.5, 5.5, 3.5, 2.5, 2.5]   # BAR BRD CLR DRU FTR MNK PAL RNG ROG SOR WIZ (IWD2)
KOSC_KIT = {'NPC_WARRIOR': 4.5, 'NPC_EXPERT': 3.5, 'NPC_ADEPT': 3.5}
SZAB = {  # szablon: (kosc, bez KON)
    'SZ_SKELETON': (6.5, True), 'SZ_ZOMBIE': (6.5, True), 'SZ_GHOST': (6.5, True),
    'SZ_HALFDRAGON': (5.5, False), 'SZ_LYCANTHROPE': (4.5, False)}

def szablon(c):
    n = (c['name'] or '').lower().strip()
    if re.search(r'skelet|boneguard|cold bones|demon knight', n) and 'scavenger' not in n: return 'SZ_SKELETON'
    if re.search(r'zombie|dread warrior', n): return 'SZ_ZOMBIE'
    if re.search(r"^ghost$|hunter's ghost|kyosti's ghost|egenia's spirit", n): return 'SZ_GHOST'
    if re.search(r'half.?dragon', n): return 'SZ_HALFDRAGON'
    if re.search(r'^(greater )?were(wolf|rat)', n): return 'SZ_LYCANTHROPE'
    return None

def tylko_ftr(c): return c['lvl'][4] > 0 and sum(c['lvl']) == c['lvl'][4]

EKSPERT = r'worker|laborer|dockhand|sailor|noble|huntsman|sapper|scout|child|boy|girl|prisoner|trainee|recruit'
POMIN = r'trap|bridge|hint|voice|beetle'
def klasa_npc(c):
    if sum(SP.get(c['res'], [0])): return 'NPC_ADEPT'
    if re.search(EKSPERT, (c['name'] or '').lower()): return 'NPC_EXPERT'
    return 'NPC_WARRIOR'

def podziel(lvl, ile):
    """poziomy klas przeskalowane do sumy ile (najwieksze reszty)"""
    s = sum(lvl)
    if s == 0 or ile <= 0: return [0] * 11
    q = [v * ile / s for v in lvl]
    w = [int(x) for x in q]
    for i in sorted(range(11), key=lambda i: -(q[i] - w[i]))[:ile - sum(w)]: w[i] += 1
    return w

def cr_nowe(c, hp):
    cr = c['cr']
    if not cr: return '*'
    old = A[c['res']]['hp'] or 0
    if old and hp >= 1.6 * old: return str(cr + 1)
    if old and hp <= 0.6 * old and cr > 1: return str(cr - 1)
    return '*'

wiersze = []; stat = {}
def dodaj(res, kit, szab, lv, hp, cechy, cr):
    wiersze.append([res, kit, szab] + [str(x) for x in lv] + [str(hp)] + cechy + [cr])
    k = szab if szab != '*' else kit
    stat[k] = stat.get(k, 0) + 1

for res, c in sorted(C.items()):
    st = stary.get(res)
    sz = szablon(c)
    if sz and c['tot'] >= 1 and sum(c['lvl']) == c['tot']:
        L = c['tot']; kl = math.ceil(L / 2); sl = L - kl
        if tylko_ftr(c):
            kit = 'NPC_WARRIOR'; lv = [0] * 11; lv[4] = kl; kosci = KOSC_KIT[kit] * kl
        else:
            kit = '*'; lv = podziel(c['lvl'], kl); kosci = sum(KOSC_KL[i] * v for i, v in enumerate(lv))
        if sl: lv[0] += sl
        else: sz = '*'
        kosc, bezkon = SZAB.get(sz, (0, False))
        con = 0 if (bezkon or (sz == '*' and szablon(c) in ('SZ_SKELETON', 'SZ_ZOMBIE', 'SZ_GHOST'))) else (A[res]['stats'][4] - 10) // 2
        hp = max(L, int(kosci + kosc * sl + 0.5) + con * L)
        cechy = ['*'] * 6   # szablon: cechy z CRE (baza rozna od wzorca MM)
        dodaj(res, kit, sz, lv, hp, cechy, cr_nowe(c, hp))
        continue
    if st:  # klasa potwora (test45/46) bez zmian; poziomy wojownika jak w CRE
        lv = [0] * 11; lv[4] = c['lvl'][4]
        dodaj(res, st[0], '*', lv, st[1], st[2:8], st[8]); continue
    anim = str(A[res]['anim'])
    if (c['gen'] == 1 and c['cls'] == 5 and tylko_ftr(c) and c['name']
            and not re.search(POMIN, c['name'].lower())):
        kit = klasa_npc(c); L = c['tot']
        if re.search(r'peasant|commoner', anim.lower()) and kit == 'NPC_WARRIOR': kit = 'NPC_EXPERT'   # decyzja wlasciciela
        lv = [0] * 11; lv[KIT_KL[kit] - 1] = L
        hp = max(L, int(KOSC_KIT[kit] * L + 0.5) + (A[res]['stats'][4] - 10) // 2 * L)
        dodaj(res, kit, '*', lv, hp, ['*'] * 6, cr_nowe(c, hp))

kol = ['KIT', 'SZAB'] + [f'L{i}' for i in range(1, 12)] + ['HP', 'STR', 'INT', 'WIS', 'DEX', 'CON', 'CHA', 'CR']
out = ['2DA V1.0', '*', ' ' * 15 + ''.join(f'{k:<16}' if i < 2 else f'{k:<6}' for i, k in enumerate(kol))]
for w in wiersze:
    out.append(f'{w[0]:<15}' + ''.join(f'{v:<16}' if i < 2 else f'{v:<6}' for i, v in enumerate(w[1:])))
open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/dnd/DSPOTWOR.2DA', 'w', newline='').write('\n'.join(o.rstrip() for o in out) + '\n')
json.dump(wiersze, open('/tmp/dnd/npc_szablony.json', 'w'))
print(len(wiersze), sorted(stat.items()))

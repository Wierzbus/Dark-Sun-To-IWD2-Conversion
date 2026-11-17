"""test48: klasy potworow, nieumarly wojownik, klasy NPC i szablony -> DSPOTWOR.2DA (komponent 8).

Wejscie: DSPOTWOR.2DA z test46 (kolumny KIT HP cechy CR; /tmp/dnd/DSPOTWOR_t46.2DA) i dane CRE gry
(/tmp/dnd/cre_ids.json, cre_iwd2.json, cre_czary.json - wyciagniete z CRE.bif).
Wyjscie: kolumny KIT SZAB L1..L11 HP STR INT WIS DEX CON CHA CR CECHA
  KIT   - ukryta podklasa klasy podstawowej (MON_*, NPC_*) albo * (klasy CRE bez podklasy)
  SZAB  - ukryta podklasa szablonu na klasie 1 (tylko SZ_LYCANTHROPE - jedyny szablon z kosciami) albo *
  L1..L11 - poziomy klas BAR..WIZ; suma = dotychczasowy poziom CRE
  CECHA - przedmiot cech szablonu do wolnego slotu 4 (jak 00CIDEAD w grze) albo *
Szablony, ktore w D&D zostawiaja poziomy klasy (duch, polsmok; w przyszlosci wampir, lisz, rycerz smierci):
klasy CRE bez zmian, kosc PW szablonu (duch k12 bez KON, polsmok o stopien wieksza), cechy z przedmiotu.
"""
import json, re, sys
STARY = '/tmp/dnd/DSPOTWOR_t46.2DA'
C = {c['res']: c for c in json.load(open('/tmp/dnd/cre_ids.json'))}
A = {c['res'].upper(): c for c in json.load(open('/tmp/dnd/cre_iwd2.json'))}
SP = json.load(open('/tmp/dnd/cre_czary.json'))
stary = {}
for l in open(STARY).read().split('\n')[3:]:
    p = l.split()
    if len(p) == 10: stary[p[0].upper()] = p[1:]

KIT_KL = {'NPC_WARRIOR': 5, 'NPC_EXPERT': 9, 'NPC_ADEPT': 3}
KOSC_KL = [12, 6, 8, 8, 10, 8, 10, 10, 6, 4, 4]           # BAR BRD CLR DRU FTR MNK PAL RNG ROG SOR WIZ (IWD2)
KOSC_KIT = {'NPC_WARRIOR': 8, 'NPC_EXPERT': 6, 'NPC_ADEPT': 6}
sr = lambda k: (k + 1) / 2
mod = lambda x: (x - 10) // 2

def tylko_ftr(c): return c['lvl'][4] > 0 and sum(c['lvl']) == c['lvl'][4]

def nieumarly_wojownik(n):
    return re.search(r'boneguard|armored skeleton|skeleton archer|cold bones|demon knight|dread warrior', n)
def szablon_cech(n):       # szablony zachowujace poziomy klasy
    if re.search(r"^ghost$|hunter's ghost|kyosti's ghost|egenia's spirit", n): return 'duch'
    if re.search(r'half.?dragon', n): return 'polsmok'
    return None
LYK = [(r'^greater werewolf', 6), (r'^werewolf', 2), (r'^wererat', 1)]   # kosci zwierzecia: wilk straszny 6, wilk 2, szczur 1

# cechy z MM I (1st-Level Warrior / bloki ras) dla ogolnych humanoidow; wartosc = max(CRE, MM)
MM = {'orc': (17, 8, 7, 11, 12, 6), 'goblin': (11, 10, 9, 13, 12, 6), 'hobgoblin': (13, 10, 9, 13, 14, 8),
      'bugbear': (15, 10, 10, 12, 13, 9), 'gnoll': (15, 8, 11, 10, 13, 8), 'lizard': (13, 9, 12, 10, 13, 10),
      'duergar': (13, 10, 9, 11, 14, 4), 'drow': (13, 12, 9, 13, 10, 10)}       # kolejnosc CRE: SIL INT MDR ZR KON CHA
def rasa_mm(n):
    if re.search(r'half|orog', n): return None
    for k in ('hobgoblin', 'goblin', 'bugbear', 'gnoll', 'lizard', 'duergar', 'drow', 'orc'):
        if re.search(r'\b' + k, n): return k
    return None

EKSPERT = r'worker|laborer|dockhand|sailor|noble|huntsman|sapper|scout|child|boy|girl|prisoner|trainee|recruit'
POMIN = r'trap|bridge|hint|voice|beetle'
def klasa_npc(c, anim):
    if sum(SP.get(c['res'], [0])): return 'NPC_ADEPT'
    if re.search(EKSPERT, (c['name'] or '').lower()) or re.search(r'peasant|commoner', anim.lower()): return 'NPC_EXPERT'
    return 'NPC_WARRIOR'

def cr_nowe(c, hp):
    cr = c['cr']
    if not cr: return '*'
    old = A[c['res']]['hp'] or 0
    if old and hp >= 1.6 * old: return str(cr + 1)
    if old and hp <= 0.6 * old and cr > 1: return str(cr - 1)
    return '*'

wiersze = []; stat = {}
def dodaj(res, kit, szab, lv, hp, cechy, cr, cecha='*', tag=None):
    wiersze.append([res, kit, szab] + [str(x) for x in lv] + [str(hp)] + cechy + [cr, cecha])
    k = tag or (szab if szab != '*' else kit); stat[k] = stat.get(k, 0) + 1

for res, c in sorted(C.items()):
    n = (c['name'] or '').lower().strip(); st = stary.get(res); s = A[res]['stats']; L = c['tot']
    if sum(c['lvl']) != L or not L: continue
    # 1. uzbrojeni nieumarli (decyzja wlasciciela): MON_UNDEAD_W, caly poziom
    if nieumarly_wojownik(n) and tylko_ftr(c):
        hp = max(L, int(sr(12) * L + 0.5)); lv = [0] * 11; lv[4] = L
        dodaj(res, 'MON_UNDEAD_W', '*', lv, hp, ['*'] * 6, cr_nowe(c, hp)); continue
    # 2. szablony zachowujace klasy: duch, polsmok
    sc = szablon_cech(n)
    if sc:
        kit = 'NPC_WARRIOR' if tylko_ftr(c) else '*'
        lv = list(c['lvl'])
        kosci = [KOSC_KIT['NPC_WARRIOR'] if (kit != '*' and i == 4) else KOSC_KL[i] for i in range(11)]
        if sc == 'duch': hp = int(sum(sr(12) * v for v in lv) + 0.5)
        else: hp = int(sum(sr(min(12, kosci[i] + 2)) * v for i, v in enumerate(lv)) + 0.5) + mod(s[4]) * L
        hp = max(L, hp)
        cecha = '00CIDRG1' if sc == 'polsmok' else '*'
        dodaj(res, kit, '*', lv, hp, ['*'] * 6, cr_nowe(c, hp), cecha, tag='szablon_' + sc); continue
    # 3. likantropy: klasa humanoida + kosci zwierzecia (SZ_LYCANTHROPE na klasie 1)
    lk = next((k for p, k in LYK if re.search(p, n)), None)
    if lk and tylko_ftr(c):
        z = min(lk, L - 1) if L > 1 else 0; lv = [0] * 11; lv[4] = L - z; lv[0] = z
        hp = max(L, int(sr(8) * L + 0.5) + mod(s[4]) * L)
        dodaj(res, 'NPC_WARRIOR', 'SZ_LYCANTHROPE' if z else '*', lv, hp, ['*'] * 6, cr_nowe(c, hp)); continue
    # 4. klasy potworow z test45/46 (zwykle szkielety i zombie - MON_UNDEAD jak w D&D)
    if st:
        lv = [0] * 11; lv[4] = c['lvl'][4]
        dodaj(res, st[0], '*', lv, st[1], st[2:8], st[8]); continue
    # 5. humanoidy z samymi poziomami wojownika: klasa NPC, cechy z MM dla ogolnych przedstawicieli ras
    anim = str(A[res]['anim'])
    if c['gen'] == 1 and c['cls'] == 5 and tylko_ftr(c) and c['name'] and not re.search(POMIN, n):
        kit = klasa_npc(c, anim); lv = [0] * 11; lv[KIT_KL[kit] - 1] = L
        r = rasa_mm(n); cechy = ['*'] * 6; s2 = list(s)
        if r:
            nowe = [max(a, b) for a, b in zip(s, MM[r])]
            cechy = [str(v) if v != a else '*' for v, a in zip(nowe, s)]; s2 = nowe
        hp = max(L, int(sr(KOSC_KIT[kit]) * L + 0.5) + mod(s2[4]) * L)
        dodaj(res, kit, '*', lv, hp, cechy, cr_nowe(c, hp))

kol = ['KIT', 'SZAB'] + [f'L{i}' for i in range(1, 12)] + ['HP', 'STR', 'INT', 'WIS', 'DEX', 'CON', 'CHA', 'CR', 'CECHA']
fmt = lambda i, v: f'{v:<16}' if i < 2 else f'{v:<6}'
out = ['2DA V1.0', '*', ' ' * 15 + ''.join(fmt(i, k) for i, k in enumerate(kol))]
for w in wiersze: out.append(f'{w[0]:<15}' + ''.join(fmt(i, v) for i, v in enumerate(w[1:])))
open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/dnd/DSPOTWOR.2DA', 'w', newline='').write('\n'.join(o.rstrip() for o in out) + '\n')
print(len(wiersze), sorted(stat.items()))

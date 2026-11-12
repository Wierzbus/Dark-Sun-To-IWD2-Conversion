"""Deasembler kodu bajtowego GPL (skrypty GPL/MAS w GPLDATA.GFF).

Port do Pythona z OpenDS `tools/gpl-disasm/src/lib.rs` (MIT, Brandon LaRocque,
https://github.com/VirInvictus/opends), ktory z kolei przenosi katalog opcodow,
`gpl_read_number` i dekoder napisow z dsoageofheroes/libgff `src/gpl/parse.c` oraz
soloscuro-archive `src/gpl/gpl-string.c` (MIT). Zakres: tabela opcodow, liczba
parametrow, wyrazenia, napisy, menu, search, setrecord, load variable. Bez CFG z OpenDS;
zamiast tego `reachable()` przechodzi graf skokow w obrebie skryptu.
"""
from __future__ import annotations

from dataclasses import dataclass, field

EXTENDED_VAR = 0x40
OP_LOW, OP_HIGH = 0xD0, 0xDF
OPEN_PAREN, CLOSE_PAREN = 0xE2, 0xE1
IMMED_BIGNUM, RETVAL, IMMED_BYTE, IMMED_WORD, IMMED_NAME, IMMED_STRING = 0x0B, 0x0C, 0x0F, 0x10, 0x11, 0x12
VAR_KINDS = {0x01: "LSTR", 0x02: "LNUM", 0x03: "LBYTE", 0x04: "LNAME", 0x05: "LBN", 0x06: "GSTR",
             0x07: "GNUM", 0x08: "GBYTE", 0x09: "GNAME", 0x0A: "GBN", 0x0D: "GF", 0x0E: "LF"}
OPS = {0xD1: "+", 0xD2: "-", 0xD3: "*", 0xD4: "/", 0xD5: "and", 0xD6: "or", 0xD7: "==", 0xD8: "!=",
       0xD9: ">", 0xDA: "<", 0xDB: ">=", 0xDC: "<=", 0xDD: "&", 0xDE: "|", 0xDF: "bclr"}
RETVAL_SAFE = {0x0F, 0x10, 0x1A, 0x1E, 0x1F, 0x20, 0x22, 0x25, 0x2F, 0x33, 0x34, 0x38, 0x39, 0x3D,
               0x41, 0x49, 0x52, 0x59, 0x5A, 0x5C, 0x80}
MAX_RETVAL_DEPTH = 4

NAMES = """zero|long divide equal|byte dec|word dec|long dec|byte inc|word inc|long inc|hunt|getxy|
string copy|p damage|changemoney|setvar|toggle accum|getstatus|getlos|long times equal|jump|local sub|
global sub|local ret|load variable|compare|load accum|global ret|nextto|inlostrigger|notinlostrigger|
clear los|nametonum|numtoname|bitsnoop|award|request|source trace|shop|clone|default|ifcompare|
trace var|orelse|clearpic|continue|log|damage|source line num|drop|passtime|exit gpl|fetch|search|
getparty|fight|flee|follow|getyn|give|go|input bignum|goxy|readorders|if|else|setrecord|setother|
input string|input number|input money|joinparty|leaveparty|lockdoor|menu|setthing|default|
local sub trace|default|default|default|print string|print number|printnl|rand|default|showpic|
default|default|default|skillroll|statroll|string compare|match string|take|sound|tport|music|
default|cmpend|wait|while|wend|attacktrigger|looktrigger|endif|move tiletrigger|door tiletrigger|
move boxtrigger|door boxtrigger|pickup itemtrigger|usetrigger|talktotrigger|noorderstrigger|
usewithtrigger|default|default|default|default|default|byte plus equal|byte minus equal|
byte times equal|byte divide equal|word plus equal|word minus equal|word times equal|
word divide equal|long plus equal|long minus equal|get range"""
OPCODES = [n.strip() for n in NAMES.replace("\n", "").split("|")]
assert len(OPCODES) == 0x81

# Liczba parametrow (wyrazen) na opcode; None = brak, 'C' = nieznany ksztalt (best effort),
# pozostale litery: L log, V load variable, M menu, S search, R setrecord.
_P = {0x00: 0, 0x0D: "C", 0x0E: 0, 0x15: 0, 0x16: "V", 0x19: 0, 0x23: "C", 0x26: "C", 0x28: "C",
      0x2A: 0, 0x2B: 0, 0x2C: "L", 0x2E: "C", 0x31: 0, 0x33: "S", 0x35: 0, 0x38: 0, 0x3B: "C",
      0x40: "R", 0x45: "C", 0x46: "C", 0x47: "C", 0x48: "M", 0x4A: "C", 0x4B: "C", 0x4C: "C",
      0x4D: "C", 0x4E: "C", 0x51: 0, 0x53: "C", 0x55: "C", 0x56: "C", 0x57: "C", 0x58: "C", 0x5B: "C",
      0x60: "C", 0x61: 0, 0x67: 0, 0x71: "C", 0x72: "C", 0x73: "C", 0x74: "C", 0x75: "C"}
_N = {0x01: 2, 0x0A: 2, 0x0B: 2, 0x10: 3, 0x11: 2, 0x14: 2, 0x1A: 2, 0x1B: 4, 0x1C: 4, 0x20: 2,
      0x21: 2, 0x22: 4, 0x25: 6, 0x27: 2, 0x2D: 2, 0x2F: 3, 0x32: 2, 0x37: 2, 0x39: 4, 0x3A: 2,
      0x3C: 3, 0x49: 2, 0x4F: 2, 0x50: 2, 0x59: 3, 0x5A: 2, 0x5C: 4, 0x5E: 5, 0x65: 3, 0x66: 3,
      0x68: 5, 0x69: 5, 0x6A: 7, 0x6B: 7, 0x6C: 3, 0x6D: 3, 0x6E: 3, 0x6F: 3, 0x70: 4}
PARAMS = [(_P[i] if i in _P else _N.get(i, 1) if 0x76 > i or i > 0x80 else 2) for i in range(0x81)]

TRIGGERS = {0x65: "atak", 0x66: "ogledziny", 0x6C: "podniesienie", 0x6D: "uzycie", 0x6E: "rozmowa",
            0x6F: "brak rozkazow", 0x70: "uzycie z"}


class BestEffort(Exception):
    pass


@dataclass
class Tok:
    kind: str          # imm, var, name, str, op, paren, retval, complex, big, byte
    value: object = None


@dataclass
class Ins:
    offset: int
    opcode: int
    params: list = field(default_factory=list)  # lista list Tok
    length: int = 0

    @property
    def name(self):
        return OPCODES[self.opcode] if self.opcode < len(OPCODES) else f"op{self.opcode:02x}"


def decode_compressed(b: bytes, p: int):
    """7 bitow od najstarszego, kod 3 konczy (soloscuro-archive read_compressed)."""
    buf, idx, out, i = 0, 1, [], p
    while len(out) < 1024 and i < len(b):
        if idx > 0:
            buf = ((buf << 8) & 0xFF00) | b[i]
            i += 1
        ch = (buf >> idx) & 0x7F
        if ch == 3:
            return "".join(map(chr, out)), i - p
        out.append(ch)
        idx = idx + 1 if idx < 7 else 0
    raise BestEffort("napis bez terminatora")


def read_text(b: bytes, p: int):
    m = b[p]
    if m == 0x01:
        return "<imie_rozmowcy>", 1
    if m == 0x02:
        return "<nieskompresowany>", 1
    if m == 0x05:
        s, n = decode_compressed(b, p + 1)
        return s, 1 + n
    raise BestEffort(f"nieznany typ napisu {m:#x}")


def _complex(b, p):
    obj = (b[p] << 8) | b[p + 1]
    depth = b[p + 2]
    return Tok("complex", (obj, list(b[p + 3:p + 3 + depth]))), 3 + depth


def read_expr(b: bytes, p: int, depth: int = 0):
    start, toks, paren = p, [], 0
    while True:
        if p >= len(b):
            raise BestEffort("koniec danych w wyrazeniu")
        cop = b[p]
        p += 1
        nxt = False
        if cop < 0x80:
            toks.append(Tok("imm", (cop << 8) | b[p]))
            p += 1
        else:
            ext = cop < OP_LOW and (cop & EXTENDED_VAR) != 0
            disp = cop & ~EXTENDED_VAR if ext else cop
            tag = disp & 0x7F
            if tag in VAR_KINDS and disp < OP_LOW:
                vid = b[p]
                p += 1
                if ext:
                    vid = vid * 256 + b[p]
                    p += 1
                toks.append(Tok("var", (VAR_KINDS[tag], vid)))
            elif disp == IMMED_BIGNUM | 0x80:
                hi, lo = (b[p] << 8) | b[p + 1], (b[p + 2] << 8) | b[p + 3]
                toks.append(Tok("big", (hi << 16) + lo))
                p += 4
            elif disp == RETVAL | 0x80:
                inner = b[p]
                p += 1
                if depth >= MAX_RETVAL_DEPTH or inner not in RETVAL_SAFE:
                    raise BestEffort(f"retval {inner:#x}")
                params, n = read_params(inner, b, p, depth + 1)
                p += n
                toks.append(Tok("retval", (inner, params)))
            elif disp == IMMED_BYTE | 0x80:
                v = b[p]
                toks.append(Tok("byte", v - 256 if v > 127 else v))
                p += 1
            elif disp == IMMED_WORD | 0x80:
                raise BestEffort("immed word")
            elif disp == IMMED_NAME | 0x80:
                toks.append(Tok("name", -((b[p] << 8) | b[p + 1])))
                p += 2
            elif disp == IMMED_STRING | 0x80:
                s, n = read_text(b, p)
                toks.append(Tok("str", s))
                p += n
            elif disp == OPEN_PAREN:
                paren += 1
                toks.append(Tok("paren", "("))
                nxt = True
            elif disp == CLOSE_PAREN:
                paren -= 1
                toks.append(Tok("paren", ")"))
            elif OP_LOW < disp <= OP_HIGH:
                toks.append(Tok("op", OPS[disp]))
                nxt = True
            elif 0xB0 <= disp <= 0xBF:
                t, n = _complex(b, p)
                toks.append(t)
                p += n
            else:
                raise BestEffort(f"bajt wyrazenia {cop:#x}")
        if not nxt and p < len(b) and OP_LOW < b[p] <= OP_HIGH:
            nxt = True
        if not nxt and paren <= 0:
            return toks, p - start


def read_params(op: int, b: bytes, p: int, depth: int = 0):
    start = p
    spec = PARAMS[op] if op < len(PARAMS) else "C"
    params = []
    if spec == "C":
        raise BestEffort(f"opcode {op:#x} o nieznanym ksztalcie")
    if isinstance(spec, int):
        for _ in range(spec):
            t, n = read_expr(b, p, depth)
            params.append(t)
            p += n
    elif spec == "L":
        s, n = read_text(b, p)
        params.append([Tok("str", s)])
        p += n
    elif spec == "V":
        t, n = read_expr(b, p, depth)
        params.append(t)
        p += n
        raw = b[p] & 0x7F
        ext = (raw & EXTENDED_VAR) != 0
        dt = raw & ~EXTENDED_VAR if ext else raw
        p += 1
        if dt < 0x10:
            if dt not in VAR_KINDS:
                raise BestEffort("load variable: typ")
            vid = b[p]
            p += 1
            if ext:
                vid = vid * 256 + b[p]
                p += 1
            params.append([Tok("var", (VAR_KINDS[dt], vid))])
        else:
            t, n = _complex(b, p)
            params.append([t])
            p += n
    elif spec == "R":
        t, n = _complex(b, p)
        params.append([t])
        p += n
        t, n = read_expr(b, p, depth)
        params.append(t)
        p += n
    elif spec == "M":
        t, n = read_expr(b, p, depth)
        params.append(t)
        p += n
        items = 0
        while items < 24 and p < len(b) and b[p] != 0x4A:
            for _ in range(3):
                t, n = read_expr(b, p, depth)
                params.append(t)
                p += n
            items += 1
        if p < len(b) and b[p] == 0x4A:
            p += 1
    elif spec == "S":
        t, n = read_expr(b, p, depth)
        params.append(t)
        p += n + 2
        while True:
            if p < len(b) and b[p] == 0x53:
                p += 1
            typ = b[p + 1]
            p += 2
            if 4 <= typ <= 6:
                t, n = read_expr(b, p, depth)
                params.append(t)
                p += n
            if p >= len(b) or b[p] != 0x53:
                break
    return params, p - start


def disassemble(b: bytes) -> tuple[list[Ins], bool]:
    """Liniowy przebieg; zwraca (instrukcje, czy_wyrownany_do_konca)."""
    out, p = [], 0
    while p < len(b):
        op = b[p]
        try:
            params, n = read_params(op, b, p + 1)
        except (BestEffort, IndexError):
            out.append(Ins(p, op, [], 1))
            return out, False
        out.append(Ins(p, op, params, 1 + n))
        p += 1 + n
    return out, True


def literal(toks) -> int | None:
    if len(toks) == 1 and toks[0].kind in ("imm", "byte", "big", "name"):
        return toks[0].value
    return None


def strings_of(ins: Ins) -> list[str]:
    out = []

    def walk(toks):
        for t in toks:
            if t.kind == "str":
                out.append(t.value)
            elif t.kind == "retval":
                for ps in t.value[1]:
                    walk(ps)
    for ps in ins.params:
        walk(ps)
    return out


TERMINATE = {0x00, 0x15, 0x19, 0x31}  # zero, local ret, global ret, exit gpl


def reachable(instrs: list[Ins], start: int) -> list[Ins]:
    """Instrukcje osiagalne od offsetu `start` w obrebie skryptu (skoki, if/else, while,
    menu, local sub); bez wchodzenia w global sub. Kolejnosc wg offsetu."""
    at = {i.offset: k for k, i in enumerate(instrs)}
    seen, todo = set(), [start]
    while todo:
        off = todo.pop()
        k = at.get(off)
        while k is not None and k not in seen:
            seen.add(k)
            ins = instrs[k]
            op = ins.opcode
            tgt = [literal(p) for p in ins.params]
            if op == 0x12 and tgt and tgt[0] is not None:            # jump
                todo.append(tgt[0])
                break
            if op in (0x3E, 0x63, 0x3F, 0x64, 0x13) and tgt and tgt[0] is not None:
                todo.append(tgt[0])
                if op in (0x3F, 0x64):                                # else, wend: skok bezwarunkowy
                    break
            if op == 0x27 and len(tgt) > 1 and tgt[1] is not None:    # ifcompare
                todo.append(tgt[1])
            if op == 0x48:                                            # menu: (tekst, cel, flaga) * n
                for j in range(2, len(tgt), 3):
                    if tgt[j] is not None:
                        todo.append(tgt[j])
            if op in TERMINATE:
                break
            k = k + 1 if k + 1 < len(instrs) else None
    return [instrs[k] for k in sorted(seen)]

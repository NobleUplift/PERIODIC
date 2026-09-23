#!/usr/bin/env python3
"""Generate src/mkdata.txt: a TI-BASIC program that stores element data as
one list per field, taken from the Disp strings of the element programs.

    python3 tools/build-mkdata.py [N]      # atomic numbers 1-N (default 110)
    python3 tools/ti89-pack.py src/mkdata.txt periodic.mkdata.89p

Values that can't be read are stored as "?" and listed in
src/mkdata-notes.txt. Supply them in src/manual-values.txt, one per line:

    <atomic number><TAB><list name><TAB><value>

Manual values override anything read from the element programs.
"""
import glob
import re
import sys

import ti89charset

# The 23 strings each element program displays, in order, with the list
# that stores the value and the label to strip. periodic\table supplies
# the labels when displaying.
FIELDS = [
    ("elnm",   r"Name:"),
    ("elsym",  r"Symbol:"),              # value split into elsym and elgrp
    (None,     r"Atomic Number:"),       # the list index itself
    ("elwt",   r"Atomic (?:Weight|Mass):?"),
    ("eltype", r"Type:"),
    ("elcfg",  None),                    # electron configuration, no label
    ("elbp",   r"Boiling Point,? ?\(K\) *="),
    ("elmp",   r"Melting Point,? ?\(K\) *="),
    ("elox",   r"Oxydation St(?:ates|ts) *="),
    ("eldens", r"Density *="),
    ("elsom",  r"SoM *="),
    ("elcrad", r"Covalent Radius,[Aa] *="),
    ("elarad", r"Atomic +Radius,[Aa] *="),
    ("elavol", r"Atomic +Volume *="),
    ("elfipv", r"FIPV *="),
    ("elshc",  r"SHC *="),
    ("elcs",   r"CS *="),
    ("elen",   r"EN *="),
    ("elhov",  r"HoV *="),
    ("elhof",  r"HoF *="),
    ("elec",   r"EC *="),
    ("eltc",   r"TC *="),
    ("elabp",  r"ABP *="),
]

LISTS = ["elnm", "elsym", "elgrp"] + [v for v, _ in FIELDS[3:] if v]

NOT_ELEMENTS = {"periodic", "atomnum", "template", "table", "mkdata"}

# Toolbar strings that precede the data in a compiled element program.
MENU = ["1st set", "2nd set", "3rd set", "4th set", "Options", "Main",
        "Next by Num.", "Prev by Num.", "Next by Name", "Prev by Name",
        "Next by Sym.", "Prev by Sym.", "Quit"]

UNKNOWN = "?"


def displayed_strings(path):
    """The strings an element program displays, in program order."""
    d = open(path, "rb").read()
    n = int.from_bytes(d[0x56:0x58], "big")
    body = d[0x58:0x58 + n]
    if body[-2] == 0x08:  # stored as text: the first four Disp lines
        text = ti89charset.decode(body.split(b"\0", 1)[0])
        lines = [l for l in text.split("\n") if l.startswith("Disp ")][:4]
        return [s for l in lines for s in re.findall(r'"([^"]*)"', l)]
    # Compiled: strings are stored as 00 <chars> 00 2D (STR_DATA_TAG), and
    # the byte-code runs backwards, so reverse them to get program order.
    strings = [ti89charset.decode(m.group(1))
               for m in re.finditer(rb"\x00([^\x00]*)\x00\x2d", body)][::-1]
    if strings[:len(MENU)] == MENU:
        strings = strings[len(MENU):]
    return strings


def parse(path, strings, notes):
    """Match each field by label, at its usual position or anywhere else."""
    name = path.split(".")[1]
    rec, used = {}, set()
    for pos, (var, label) in enumerate(FIELDS):
        here = strings[pos] if pos < len(strings) else None
        if label is None:  # electron configuration: no label to check
            if here is None or re.match(r"[A-Za-z ]+[:=]", here):
                notes.append("%s: electron configuration: expected at position %d, found %r"
                             % (name, pos + 1, here))
                rec[var] = UNKNOWN
            else:
                rec[var] = here
                used.add(pos)
            continue
        if here is not None and re.match(label, here):
            hit = here
        else:
            hits = [s for s in strings if re.match(label, s)]
            if len(hits) == 1:
                hit = hits[0]
            else:
                notes.append("%s: %s: no string matching %r (position %d holds %r)"
                             % (name, var or "atomic number", label, pos + 1, here))
                if var == "elsym":
                    rec["elsym"] = rec["elgrp"] = UNKNOWN
                elif var:
                    rec[var] = UNKNOWN
                continue
        used.add(strings.index(hit))
        value = re.sub("^" + label, "", hit).strip()
        # A run of 2+ spaces separates values, e.g. "Symbol:H         -1/IA".
        parts = re.split(r"\s{2,}", value)
        if var == "elsym":
            if len(parts) == 2:
                rec["elsym"], rec["elgrp"] = parts[0], parts[1].lstrip("-")
            else:
                notes.append("%s: cannot split symbol and group in %r" % (name, hit))
                rec["elsym"] = rec["elgrp"] = UNKNOWN
        elif var is None:
            rec["num"] = int(value) if value.isdigit() else None
        else:
            if len(parts) > 1:
                notes.append("%s: %s: value %r has a run of spaces; stored as is"
                             % (name, var, value))
            rec[var] = value
    for pos, extra in enumerate(strings[:len(FIELDS) + 2]):
        if pos not in used:
            notes.append("%s: string %d not used: %r" % (name, pos + 1, extra))
    return rec


def load_manual(path="src/manual-values.txt"):
    manual = {}
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return manual
    for i, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not parts[0].isdigit() or parts[1] not in LISTS:
            sys.exit("%s:%d: expected <number><TAB><list name><TAB><value>" % (path, i))
        manual[(int(parts[0]), parts[1])] = parts[2]
    return manual


def ti_list(items):
    return "{" + ",".join(items) + "}"


def ti_str(s):
    if '"' in s:
        sys.exit("string contains a quote: %r" % s)
    return '"%s"' % s


def main(count):
    notes, by_num = [], {}
    for path in sorted(glob.glob("periodic.*.89p")):
        if path.split(".")[1] in NOT_ELEMENTS:
            continue
        rec = parse(path, displayed_strings(path), notes)
        if rec.get("num") is None:
            notes.append("%s: atomic number unreadable; element skipped" % path)
        elif rec["num"] in by_num:
            notes.append("%s: atomic number %d used twice" % (path, rec["num"]))
        else:
            by_num[rec["num"]] = rec

    manual = load_manual()
    recs = []
    for n in range(1, count + 1):
        rec = by_num.get(n)
        if rec is None:
            notes.append("atomic number %d: no element program" % n)
            rec = {}
        for var in LISTS:
            if (n, var) in manual:
                rec[var] = manual[(n, var)]
            rec.setdefault(var, UNKNOWN)
        recs.append(rec)

    missing = ["%d\t%s\t" % (n, var) for n, rec in enumerate(recs, 1)
               for var in LISTS if rec[var] == UNKNOWN]
    with open("src/mkdata-notes.txt", "w", encoding="utf-8") as f:
        f.write("Generated by tools/build-mkdata.py for atomic numbers 1-%d.\n\n" % count)
        f.write("Problems reading the element programs:\n")
        f.write("".join("  %s\n" % s for s in notes) or "  none\n")
        f.write("\nValues still unknown (stored as %r). Add them to "
                "src/manual-values.txt as <number><TAB><list><TAB><value>:\n" % UNKNOWN)
        f.write("".join("%s\n" % s for s in missing) or "  none\n")

    byname = sorted(range(1, count + 1), key=lambda n: recs[n - 1]["elnm"])
    bysym = sorted(range(1, count + 1), key=lambda n: recs[n - 1]["elsym"])

    out = ["()", "Prgm",
           "© Generated by tools/build-mkdata.py. Do not edit by hand.",
           "© Item n of each list is the element with atomic number n",
           "© (1-%d). \"%s\" marks a value not yet known." % (count, UNKNOWN)]
    for var in LISTS:
        out.append(ti_list(ti_str(r[var]) for r in recs) + "→periodic\\" + var)
    out.append("© Atomic numbers sorted by name, and by symbol")
    out.append(ti_list(str(n) for n in byname) + "→periodic\\byname")
    out.append(ti_list(str(n) for n in bysym) + "→periodic\\bysym")
    out += ["ClrIO", 'Disp "Data stored for %d","elements. Now run","periodic\\table()"' % count,
            "EndPrgm"]
    open("src/mkdata.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("%d elements, %d notes, %d unknown values; see src/mkdata-notes.txt"
          % (count, len(notes), len(missing)))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 110)

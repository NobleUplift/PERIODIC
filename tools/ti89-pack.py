#!/usr/bin/env python3
"""Pack a TI-BASIC source file into a text-stored .89p program variable.

    python3 tools/ti89-pack.py src/table.txt periodic.table.89p

The source is UTF-8 with LF line endings, written in the TI character set
(→ for store, ≠ ≤ ≥, − for negation, © for comments); see ti89charset.py.
The first line is the parameter list, e.g. "()", followed by Prgm ... EndPrgm.
The folder and variable name come from the output file name
(<folder>.<name>.89p). The calculator tokenizes the program on first run.
"""
import sys

import ti89charset

# Bytes after the source text: NUL, a 2-byte big-endian editor cursor offset
# (0x0001 in most files here), Prgm command (19 E4), END_TAG (E5), 00 01,
# flag 08 (stored as text), USER_DEF_TAG (DC). Repacking the repo's
# text-stored programs with this tail reproduces them byte for byte, apart
# from the cursor offset.
TEXT_PRGM_TAIL = bytes.fromhex("00 00 01 19 e4 e5 00 01 08 dc")


def pad(s, n):
    raw = s.encode("latin-1")
    if len(raw) > n:
        raise ValueError("%r is longer than %d bytes" % (s, n))
    return raw + b"\0" * (n - len(raw))


def pack(source, folder, name, comment="Program file"):
    text = source.replace("\r\n", "\n").rstrip("\n")
    body = ti89charset.encode(text) + TEXT_PRGM_TAIL
    data = len(body).to_bytes(2, "big") + body
    checksum = (sum(data) & 0xFFFF).to_bytes(2, "little")
    total = 0x56 + len(data) + 2

    out = bytearray()
    out += b"**TI92P*"
    out += b"\x01\x00"
    out += pad(folder, 8)
    out += pad(comment, 40)
    out += (1).to_bytes(2, "little")      # one variable
    out += (0x52).to_bytes(4, "little")   # its data offset
    out += pad(name, 8)
    out += bytes([0x12, 0x00])            # type: program, attribute: none
    out += b"\x00\x00"
    out += total.to_bytes(4, "little")
    out += b"\xa5\x5a"
    out += b"\x00\x00\x00\x00"
    out += data
    out += checksum
    assert len(out) == total
    return bytes(out)


def main(src, dst):
    base = dst.rsplit("/", 1)[-1]
    folder, name, ext = base.split(".")
    if ext != "89p" or len(name) > 8 or len(folder) > 8:
        sys.exit("output must be named <folder>.<name>.89p, names up to 8 chars")
    source = open(src, encoding="utf-8").read()
    with open(dst, "wb") as f:
        f.write(pack(source, folder, name))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

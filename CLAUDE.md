# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A periodic-table browser written in 2006 in 68k TI-BASIC for the TI-89 Titanium. It works on any AMS 2.x/3.x calculator: TI-89, TI-92 Plus or Voyage 200. It has no build, lint or tests; the programs run on the calculator or in an emulator such as TiEmu. The only code that runs on a PC is `tools/ti89-textconv.py`.

## Setup: readable diffs

Every `.89p` file is a TI link-software container (a binary header and footer around the program). `.gitattributes` sends them through the `ti89` diff driver. Enable it once per clone:

```
git config include.path ../.gitconfig
```

After that, `git diff`, `git log -p` and `git show` print the program as text. To view one file directly: `python3 tools/ti89-textconv.py periodic.gold.89p`. GitHub's web UI ignores textconv and shows these files as binary.

## Architecture

All variables live in the calculator folder `periodic`, and every call is fully qualified (`periodic\gold()`). Variable names are at most 8 characters, so element names are truncated (`magnesiu`, `praseody`, `darmstad`).

- **`periodic.periodic`** (main entry point) and **`periodic.atomnum`** (look up an element by atomic number): mostly large dispatch tables that jump to `periodic\<element>()`. `atomnum` shows "False Input" or "Undiscovered Element" for invalid numbers.
- **One program per element**, Hydrogen through Darmstadtium (110 elements). Each one is a copy of `periodic.template`, a skeleton with placeholders that is itself incomplete (one `Goto` has no target, and the navigation calls are blank). Each copy contains:
  - 4 `Lbl` screens, one per toolbar "set", each shown with `ClrIO` + `Disp` of hard-coded strings:
    - identity: name, symbol, group, number, weight, type, electron configuration
    - thermal: boiling point, melting point, oxidation states, density, state of matter (SoM)
    - radii and volume, first ionization potential (FIPV), specific heat (SHC), crystal structure (CS)
    - electronegativity (EN), heats of vaporization/fusion (HoV/HoF), electrical and thermal conductivity (EC/TC), acid/base property (ABP)
  - A `Toolbar` whose Options menu has Main, Quit, and next/previous by atomic number, name and symbol.
  - Label names that vary per file (e.g. `aca`…`acd` plus a menu label like `klmn` or `abcd`). All of them must be declared in `Local`.
- **The data and the navigation order are copied into every element file.** "Next by Name" in `gold` calls `periodic\hafnium()`; "Next by Symbol" calls `periodic\boron()`. The first and last elements show "Beginning of List" or "End of List" instead of calling another program. Adding or removing an element means updating its neighbours in all three orders, plus the dispatch tables in `periodic` and `atomnum`.

## File format (`*.89p`)

The full byte layout is documented at the top of `tools/ti89-textconv.py`. In short:
- The header has the signature `**TI92P*` (TI-92 Plus; the TI-89 uses the same OS), the folder, a 40-byte comment, the variable name, the type (0x12 = program) and the attribute (3 = archived).
- The data starts at 0x56 with a 2-byte **big-endian** length, and a 2-byte little-endian checksum follows it. The checksum is the sum of the length bytes and data bytes, mod 65536.
- Most programs are stored as **source text**: CR (`\r`) line endings, TI character set (0xAD = negative sign, 0xB1 = ±), ending in NUL then `00 01 19 E4 E5 00 01 08 DC`. The `08` flag marks the program as text.
- These are stored **tokenized** (bytecode, flag `00`), so the diff driver shows them as a hex dump: `periodic`, `atomnum`, `argon`, `manganes`, `rutheniu`, `techneti`. They became tokenized after being run on the calculator. Reading them requires GCC4TI's `estack.h` tag tables. They are stored in reverse order: `E8` = new line, `E9` = end, `E4 xx` = a command.
- The comment ("Program file MM/DD/YY, HH:MM") was written by PC link software when the files were backed up on 2009-01-27. It is not part of the program and changes on every backup.

## Editing rules

- **Never edit a `.89p` file with a text editor or line-ending conversion.** Any change to the data must also update the length at 0x56, the total file size at 0x4C and the checksum, or the calculator will reject the file. Edit the bytes with a script and recompute all three. `git diff` should then show only the intended lines plus the checksum.
- Keep strings short enough for the 160-px-wide TI-89 screen (about 26 characters per `Disp` line).

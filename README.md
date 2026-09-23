# PERIODIC

A periodic-table browser for the TI-89 Titanium, written in 68k TI-BASIC in 2006. It also runs on the TI-89, TI-92 Plus and Voyage 200 (any calculator running AMS 2.x/3.x).

Each element from Hydrogen through Darmstadtium has four screens of data:

| Screen | Contents |
|---|---|
| 1st set | Name, symbol, group, atomic number, atomic weight, type, electron configuration |
| 2nd set | Boiling point, melting point, oxidation states, density, state of matter |
| 3rd set | Covalent and atomic radius, atomic volume, first ionization potential, specific heat, crystal structure |
| 4th set | Electronegativity, heats of vaporization and fusion, electrical and thermal conductivity, acid/base property |

The toolbar's **Options** menu moves to the next or previous element by atomic number, name or symbol, returns to the main menu, or quits.

## Installing and running

Send all the `.89p` files to the calculator with TI Connect or [TiLP](https://github.com/debrouxl/tilp_and_gfm). They go into the folder `periodic`. Then run this from the home screen:

```
periodic\periodic()
```

To jump straight to an element, run its program. Names longer than 8 characters are cut short, e.g. `periodic\gold()` or `periodic\magnesiu()`.

## Repository layout

| File | Purpose |
|---|---|
| `periodic.periodic.89p` | Main menu |
| `periodic.atomnum.89p` | Look up an element by atomic number |
| `periodic.<element>.89p` | One program per element (110 in total) |
| `periodic.template.89p` | Skeleton the element programs were copied from |
| `tools/ti89-textconv.py` | Git diff driver that shows `.89p` files as text |

## Readable diffs

`.89p` files wrap the program text in a binary header and footer, so by default Git shows them as binary. Run this once per clone:

```
git config include.path ../.gitconfig
```

After that, `git diff`, `git log -p` and `git show` print the header fields and the program source as ordinary text. To view one file directly:

```
python3 tools/ti89-textconv.py periodic.gold.89p
```

This needs Python 3. GitHub's web interface ignores this setting and still shows the files as binary.

## The `.89p` file format

Each file holds one calculator variable. Numbers are little-endian unless noted. The right-hand column shows the values in `periodic.actinium.89p`.

| Offset | Size | Field | Actinium |
|---|---|---|---|
| 0x00 | 8 | Signature: `**TI89**`, `**TI92P*`, `**TI92**` or `**V200**` | `**TI92P*` |
| 0x08 | 2 | Always `01 00` | `01 00` |
| 0x0A | 8 | Default folder name, padded with nulls | `periodic` |
| 0x12 | 40 | Comment, padded with nulls | `Program file 01/27/09, 00:14` |
| 0x3A | 2 | Number of variables in the file | 1 |
| 0x3C | 4 | Offset of this variable's data | 0x52 |
| 0x40 | 8 | Variable name, padded with nulls | `actinium` |
| 0x48 | 1 | Type: 0x12 program, 0x13 function, 0x0C string, 0x04 list, 0x06 matrix… | 0x12 |
| 0x49 | 1 | Attribute: 0 none, 1 locked, 2 or 3 archived | 3 (archived) |
| 0x4A | 2 | `00 00` | |
| 0x4C | 4 | Total file size | 0x540 = 1344 |
| 0x50 | 2 | Marker `A5 5A` | ✓ |
| 0x52 | 4 | `00 00 00 00` | |
| 0x56 | 2 | Data length, **big-endian** | 0x04E6 |
| 0x58 | n | Variable data | |
| end | 2 | Checksum: sum of the length bytes and data bytes, mod 65536 | `8B C3` |

Notes:

- **The signature says TI-92 Plus even though the files are named `.89p`.** The TI-89 and TI-92 Plus run the same operating system, so the files work on either.
- **The comment is added by the PC link software** when a variable is saved from the calculator; the calculator itself doesn't store comments. The date in these files is when they were backed up (27 January 2009), not when they were written.
- **Editing a file by hand** means updating the data length (0x56), the total file size (0x4C) and the checksum, or the calculator will reject it. Don't open these files in a text editor or convert their line endings.

### How programs are stored

- **Most of these programs are stored as source text.** Lines end with a carriage return (`0D`) and the text uses the TI character set (for example `AD` is the negative sign and `B1` is ±). The text ends with a null byte and then `00 01 19 E4 E5 00 01 08 DC`:
  - `DC` means a user-defined program or function.
  - `08` is a flag marking the program as stored as text.
  - `E5` ends the (empty) parameter list.
  - `19 E4` is the `Prgm` command.
- **Six programs are compiled** (`periodic`, `atomnum`, `argon`, `manganes`, `rutheniu`, `techneti`), because they were run on the calculator before being backed up. Their flag byte is `00`, and the data is TI's byte-code stored in reverse order: `E8` is a new line, `E9` the end of the program, and `E4 xx` a command. The diff driver shows these as a hex dump.
- **The meaning of the `08`/`00` flag was worked out by comparing these files**; none of the sources below document it.

### Sources

- [TI-89 Link Protocol Guide – File formats](https://merthsoft.com/linkguide/ti89/fformat.html)
- [TiLP libtifiles `files9x.cc`](https://github.com/debrouxl/tilibs/blob/master/libtifiles/trunk/src/files9x.cc) (file reader and writer)
- [TiLP libtifiles `types89.h`](https://github.com/debrouxl/tilibs/blob/master/libtifiles/trunk/src/types89.h) (variable type numbers)
- [GCC4TI `estack.h`](https://github.com/debrouxl/gcc4ti) (program byte-code tags)

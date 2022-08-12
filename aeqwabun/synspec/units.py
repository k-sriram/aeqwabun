from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, TextIO

from aeqwabun.synspec import utils

# Unit 56:


class Abundance(NamedTuple):
    iatom: int
    abn: float


def read56(text: str) -> list[Abundance]:
    """Converts the contents of a .56 file to a python list."""
    lines = text.splitlines()
    if len(lines) == 0:
        raise ValueError("unit 56 is empty")
    numlines = int(lines[0])
    if len(lines) != numlines + 1:
        raise ValueError(f"unit 56 has {len(lines)} lines, but {numlines} expected")
    abundances = [
        Abundance(int(line.split()[0]), float(line.split()[1])) for line in lines[1:]
    ]
    if len(set(x.iatom for x in abundances)) != len(abundances):
        raise ValueError("atomic numbers must be unique")
    return abundances


def read56f(file: Path) -> list[Abundance]:
    """Reads the contents of a .56 file."""
    return read56(file.read_text())


def write56(lines: list[tuple[int, float]]) -> str:
    """Converts a list of Abundances to a string storable in a .56 file."""
    abundances = []
    if len(set(line[0] for line in lines)) != len(lines):
        raise ValueError("atomic numbers must be unique")
    for line in lines:
        if line[0] < 1 or line[0] > 118:
            raise ValueError(f"atomic number {line[0]} out of range")
        if line[1] < 0 or line[1] > 1:
            raise ValueError(f"abundance {line[1]} out of range (0 to 1)")
        abundances.append(f"{line[0]} {line[1]:.6e}\n")
    return f"{len(lines)}\n" + "".join(abundances)


def write56f(file: Path | TextIO, lines: list[tuple[int, float]]) -> None:
    """Writes a list of Abundances to a .56 file."""
    content = write56(lines)
    utils.write_to_file(file, content)


# Unit 55:


@dataclass
class SynConfig:
    imode: int
    idstd: int
    iprin: int
    inmod: int
    intrpl: int
    ichang: int
    ichemc: int
    iophli: int
    nunalp: int
    nunbet: int
    nungam: int
    nunbal: int
    ifreq: int
    inlte: int
    icontl: int
    inlist: int
    ifhe2: int
    ihydpr: int
    ihe1pr: int
    ihe2pr: int
    alam0: float
    alam1: float
    cutof0: float
    cutofs: float
    relop: float
    space: float
    iunitm: list[int]
    vtb: float


def read55(text: str) -> SynConfig:
    """Converts the contents of a .55 file to a python object."""
    lines = text.splitlines()
    if len(lines) == 0:
        raise ValueError("unit 55 is empty")
    config = SynConfig(
        # Line 1
        imode=int(lines[0].split()[0]),
        idstd=int(lines[0].split()[1]),
        iprin=int(lines[0].split()[2]),
        # Line 2
        inmod=int(lines[1].split()[0]),
        intrpl=int(lines[1].split()[1]),
        ichang=int(lines[1].split()[2]),
        ichemc=int(lines[1].split()[3]),
        # Line 3
        iophli=int(lines[2].split()[0]),
        nunalp=int(lines[2].split()[1]),
        nunbet=int(lines[2].split()[2]),
        nungam=int(lines[2].split()[3]),
        nunbal=int(lines[2].split()[4]),
        # Line 4
        ifreq=int(lines[3].split()[0]),
        inlte=int(lines[3].split()[1]),
        icontl=int(lines[3].split()[2]),
        inlist=int(lines[3].split()[3]),
        ifhe2=int(lines[3].split()[4]),
        # Line 5
        ihydpr=int(lines[4].split()[0]),
        ihe1pr=int(lines[4].split()[1]),
        ihe2pr=int(lines[4].split()[2]),
        # Line 6
        alam0=float(lines[5].split()[0]),
        alam1=float(lines[5].split()[1]),
        cutof0=float(lines[5].split()[2]),
        cutofs=float(lines[5].split()[3]),
        relop=utils.fortfloat(lines[5].split()[4]),
        space=float(lines[5].split()[5]),
        # Line 7
        iunitm=[
            int(x)
            for x in lines[6].split()[1 : 1 + int(lines[6].split()[0])]  # noqa: E203
        ],
        # Line 8
        vtb=float(lines[7].split()[0]),
    )
    return config


def read55f(file: Path) -> SynConfig:
    """Reads the contents of a .55 file."""
    return read55(file.read_text())


def write55(config: SynConfig) -> str:
    """Converts a SynConfig to a string storable in a .55 file."""
    lines = [
        # Line 1
        f"{config.imode} {config.idstd} {config.iprin}",
        # Line 2
        f"{config.inmod} {config.intrpl} {config.ichang} {config.ichemc}",
        # Line 3
        f"{config.iophli} {config.nunalp} {config.nunbet} {config.nungam} "
        f"{config.nunbal}",
        # Line 4
        f"{config.ifreq} {config.inlte} {config.icontl} {config.inlist} {config.ifhe2}",
        # Line 5
        f"{config.ihydpr} {config.ihe1pr} {config.ihe2pr}",
        # Line 6
        f"{config.alam0} {config.alam1} {config.cutof0} {config.cutofs} "
        f"{config.relop:.1e} {config.space}",
        # Line 7
        "".join((f"{len(config.iunitm)}", " ".join(map(str, config.iunitm)), " 0i")),
        # Line 8
        f"{config.vtb}",
        "",
    ]
    return "\n".join(lines)


def write55f(file: Path | str | TextIO, config: SynConfig) -> None:
    """Writes a SynConfig to a .55 file."""
    utils.write_to_file(file, write55(config))


# Read the input file


def readinput(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    tokenlines = list(utils.parsefortinput(text))

    if len(tokenlines[0]) == 2:
        result["teff"] = tokenlines[0][0]
        result["grav"] = tokenlines[0][1]
    else:
        result["xmstar"] = tokenlines[0][0]
        if result["xmstar"] > 0:
            result["xmdot"] = tokenlines[0][1]
            result["rstar"] = tokenlines[0][2]
            result["reldst"] = tokenlines[0][3]
        elif result["xmstar"] == 0:
            result["teff"] = tokenlines[0][1]
            result["qgrav"] = tokenlines[0][2]
            result["dmtot"] = tokenlines[0][3]

    result["lte"] = tokenlines[1][0]
    result["ltgray"] = tokenlines[1][1]

    result["finstd"] = tokenlines[2][0]
    result["nfread"] = tokenlines[3][0]
    result["natoms"] = natoms = int(tokenlines[4][0])

    result["atoms"] = []
    for i in range(natoms):
        result["atoms"].append(
            {
                "mode": tokenlines[5 + i][0],
                "abd": tokenlines[5 + i][1],
                "modpf": tokenlines[5 + i][2],
            }
        )

    result["ions"] = []
    for line in tokenlines[5 + natoms :]:  # noqa: E203
        if line[3] == 0:
            result["ions"].append(
                {
                    "iat": line[0],
                    "iz": line[1],
                    "nlevs": line[2],
                    "ilvlin": line[4],
                    "nonstd": line[5],
                    "typion": line[6],
                    "filei": line[7],
                }
            )
    return result

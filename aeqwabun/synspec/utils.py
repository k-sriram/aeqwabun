import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence, TextIO

elements = [
    "",
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]


def symlinkf(
    src: str | Path, dst: str | Path, target_is_directory: bool = False
) -> None:
    """Symlink a file. If the file already exists, delete it first."""
    dst = Path(dst)
    if resolve_parent(dst) == resolve_parent(Path(src)):
        raise ValueError(f"src and dst are the same: {dst.resolve()}")
    if dst.exists():
        dst.unlink()
    dst.symlink_to(src, target_is_directory=target_is_directory)


def resolve_parent(path: Path) -> Path:
    """Resolve a path to its parent directory."""
    if not path.is_symlink():
        return path.resolve()
    return path.parent.resolve().joinpath(path.name)


@contextmanager
def folderlock(
    path: str | Path | None = None,
    lockfn: str = ".lock",
    unlock_after: int = 60,
    check_at_end: bool = True,
) -> Iterator[Path]:
    """
    Context manager to lock a folder.

    Parameters
    ----------
    path : str | Path
        Path to the folder to lock.
    lockfn : str
        Name of the lock file.
    unlock_after : int
        Time in seconds after which the lock is automatically removed.
    check_at_end : bool
        If True, check if the lock file is still there when the context manager
        exits. Raise RuntimeError if the file is modified.

    Returns
    -------
    path: Path
        Path to the locked folder.

    Raises
    ------
        RuntimeError
            if the lock could not be acquired or optionally if the lcokfile
            was modified midway.
    """
    _check_at_end = False
    if path is None:
        path = Path.cwd()
    else:
        path = Path(path).resolve()
    lockfile = path / lockfn
    id_ = str(uuid.uuid4())
    try:
        if (
            not lockfile.exists()
            or time.time() - lockfile.stat().st_mtime > unlock_after
        ):
            lockfile.write_text(id_)
        if lockfile.read_text() != id_:
            raise RuntimeError("Lockfile could not be acquired.")
        _check_at_end = check_at_end
        yield path
    finally:
        if _check_at_end:
            if not lockfile.exists() or lockfile.read_text() != id_:
                raise RuntimeError("Lockfile was modified")
        lockfile.unlink(missing_ok=True)


def write_to_file(file: Path | str | TextIO, content: str) -> None:
    if isinstance(file, Path):
        file.write_text(content)
    elif isinstance(file, TextIO):
        file.write(content)
    elif isinstance(file, str):
        with open(file, "w") as f:
            f.write(content)
    else:
        raise TypeError(f"file must be a Path, TextIO, or str, not {type(file)}")


def fortfloat(text: str) -> float:
    """Convert Fortran-style float to python float."""
    text = text.strip()
    if text.endswith("d"):
        text = text[:-1]
    text.replace("d", "e")
    try:
        return float(text)
    except ValueError:
        if len(text) > 1 and "-" in text[1:]:
            text = f"{text[0]}{text[1:].replace('-', 'e-')}"
            return float(text)
        else:
            raise


def tokensfort(line: str) -> Sequence[str | int | float]:
    if line == "":
        return []
    if line[0] == "*":
        return []
    if "!" in line:
        line = line[: line.index("!")]
    tokens: list[Any] = quotesplit(line.strip())
    tokens = list(filter(lambda x: x != "", tokens))
    for i, token in enumerate(tokens):
        if token in "TtFf":
            tokens[i] = token.lower() == "t"
        if token[0] == "'" and token[-1] == "'":
            tokens[i] = token[1:-1]
            continue
        if token.isdigit():
            tokens[i] = int(token)
            continue
        try:
            tokens[i] = fortfloat(token)
            continue
        except ValueError:
            pass
    return tokens


def parsefortinput(text: str) -> Iterator[Sequence[str | int | float]]:
    for line in text.splitlines():
        tokens = tokensfort(line)
        if tokens:
            yield tokens


def quotesplit(text: str, quotechar: str = "'") -> list[str]:
    """
    Split text into tokens, respecting quotes.

    Parameters
    ----------
    text : str
        Text to split.
    quotechar : str
        Quote character to use.

    Returns
    -------
    tokens : list[str]
        List of tokens.
    """
    tokens = []
    j = -1
    inquote = False
    for i, c in enumerate(text):
        if text[i] == quotechar:
            inquote = not inquote
            continue
        if not inquote and c == " ":
            if i > j + 1:
                tokens.append(text[j + 1 : i])  # noqa: E203
            j = i
    if i > j and text[-1] != " ":
        tokens.append(text[j + 1 :])  # noqa: E203
    return tokens

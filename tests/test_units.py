import tempfile
from pathlib import Path

import pytest

from aeqwabun.synspec import units


def test_read56_1() -> None:
    text = """1
8 3.847575e-03
"""
    assert units.read56(text) == [(8, 3.847575e-03)]


def test_read56_2() -> None:
    text = """0
"""
    assert units.read56(text) == []


def test_read56_3() -> None:
    text = """"""
    with pytest.raises(ValueError):
        units.read56(text)


def test_read56_4() -> None:
    text = """3
1 1.2e-04
2 1.4e-04
"""
    with pytest.raises(ValueError):
        units.read56(text)


def test_read56_5() -> None:
    """Atomic numbers must be unique."""
    with pytest.raises(ValueError):
        units.read56("2\n1 1.0e-2\n1 1.0e-3")


def test_read56f() -> None:
    file = Path("tests/models/EHeT30g4/input/fort.56")
    assert units.read56f(file) == [(8, 3.847575e-03)]


# units.write56


def test_write56_1() -> None:
    assert (
        units.write56([(8, 2.245623525e-03), (6, 1.2345e-04)])
        == "2\n8 2.245624e-03\n6 1.234500e-04\n"
    )


def test_write56_2() -> None:
    assert units.write56([]) == "0\n"


def test_write56_3() -> None:
    """Abundances must be less than 1.0."""
    with pytest.raises(ValueError):
        units.write56([(1, 2.0)])


def test_write56_4() -> None:
    """Abundances must be positive."""
    with pytest.raises(ValueError):
        units.write56([(1, 1.0e-2), (2, -1.0e-5)])


def test_write56_5() -> None:
    """Atomic numbers must be unique."""
    with pytest.raises(ValueError):
        units.write56([(1, 1.0e-2), (1, 1.0e-3)])


def test_write56f() -> None:
    try:
        _, fn = tempfile.mkstemp(suffix=".56")
        f = Path(fn)
        units.write56f(f, [(8, 3.847575e-03)])

        assert f.read_text() == "1\n8 3.847575e-03\n"
    finally:
        f.unlink()


def test_read55_1() -> None:
    text = """1 47 0
1 0 0 0
0 0 0 0 0
1 0 0 0 1
0 0 0
4465.0 4475.0 15 50 1.0-12 0.010000
0 0i
2.000000
"""
    assert units.read55(text) == units.SynConfig(
        *(
            [1, 47, 0]  # type: ignore
            + [1, 0, 0, 0]
            + [0, 0, 0, 0, 0]
            + [1, 0, 0, 0, 1]
            + [0, 0, 0]
            + [4465.0, 4475.0, 15.0, 50.0, 1.0e-12, 0.01]  # type: ignore
            + [[]]  # type: ignore
            + [2.0]  # type: ignore
        )
    )


def test_read55_2() -> None:
    text = """0 32 0
1 0 0 0
0 0 0 0 0
1 1 0 0 1
0 1 1
3000.0 6000.1 10 50 2.3e-6 0.01
1 3 0i
0.0
"""
    assert units.read55(text) == units.SynConfig(
        *(
            [0, 32, 0]  # type: ignore
            + [1, 0, 0, 0]
            + [0, 0, 0, 0, 0]
            + [1, 1, 0, 0, 1]
            + [0, 1, 1]
            + [3000.0, 6000.1, 10.0, 50.0, 2.3e-6, 0.01]  # type: ignore
            + [[3]]  # type: ignore
            + [0.0]  # type: ignore
        )
    )


def test_read55f() -> None:
    file = Path("tests/models/EHeT30g4/input/fort.55")
    assert units.read55f(file) == units.SynConfig(
        *(
            [0, 32, 0]  # type: ignore
            + [1, 0, 0, 1]
            + [0, 0, 0, 0, 0]
            + [1, 0, 0, 0, 1]
            + [0, 2, 1]
            + [3500.0, 5500.0, 15, 50, 1.0e-12, 0.01]  # type: ignore
            + [[]]  # type: ignore
            + [21.0]  # type: ignore
        )
    )


def test_write55_1() -> None:
    assert (
        units.write55(
            units.SynConfig(
                *(
                    [0, 32, 0]  # type: ignore
                    + [1, 0, 0, 1]
                    + [0, 0, 0, 0, 0]
                    + [1, 0, 0, 0, 1]
                    + [0, 2, 1]
                    + [3500.0, 5500.0, 15, 50, 1.0e-12, 0.01]  # type: ignore
                    + [[]]  # type: ignore
                    + [21.0]  # type: ignore
                )
            )
        )
        == """0 32 0
1 0 0 1
0 0 0 0 0
1 0 0 0 1
0 2 1
3500.0 5500.0 15 50 1.0e-12 0.01
0 0i
21.0
"""
    )


def test_readinput():
    with open("tests/models/hhe35lt/input/hhe35lt.5") as f:
        text = f.read()

    assert units.readinput(text) == {
        "teff": 35000.0,
        "grav": 4.0,
        "lte": True,
        "ltgray": True,
        "finstd": "",
        "nfread": 50,
        "natoms": 8,
        "atoms": [
            {"mode": 2, "abd": 0, "modpf": 0},
            {"mode": 2, "abd": 0, "modpf": 0},
            {"mode": 0, "abd": 0, "modpf": 0},
            {"mode": 0, "abd": 0, "modpf": 0},
            {"mode": 0, "abd": 0, "modpf": 0},
            {"mode": 1, "abd": 0, "modpf": 0},
            {"mode": 1, "abd": 0, "modpf": 0},
            {"mode": 1, "abd": 0, "modpf": 0},
        ],
        "ions": [
            {
                "iat": 1,
                "iz": 0,
                "nlevs": 9,
                "ilvlin": 100,
                "nonstd": 0,
                "typion": " H 1",
                "filei": "./data/h1.dat",
            },
            {
                "iat": 2,
                "iz": 0,
                "nlevs": 14,
                "ilvlin": 100,
                "nonstd": 0,
                "typion": "He 1",
                "filei": "./data/he1.dat",
            },
            {
                "iat": 2,
                "iz": 1,
                "nlevs": 14,
                "ilvlin": 100,
                "nonstd": 0,
                "typion": "He 2",
                "filei": "./data/he2.dat",
            },
        ],
    }

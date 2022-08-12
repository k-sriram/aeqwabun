import os
import shutil
import subprocess
import tempfile

import pytest

from aeqwabun.synspec.synspec import Synspec

PROJECT_ROOT = os.getcwd()
MODELS_ROOT = f"{PROJECT_ROOT}/tests/models"


def compare_files(file1: str, file2: str) -> bool:
    with open(file1, "r") as f1:
        with open(file2, "r") as f2:
            for line1, line2 in zip(f1, f2):
                if line1 != line2:
                    return False
    return True


def copy_model(model: str, files: list[str], dst: str) -> str:
    # Copy the model to the temporary directory.
    modeldir = f"{MODELS_ROOT}/{model}"
    for file in files:
        shutil.copy(f"{modeldir}/input/{file}".format(model=model), dst)
    os.symlink(f"{modeldir}/data", f"{dst}/data", target_is_directory=True)
    return modeldir


@pytest.fixture(scope="function")
def tempdir():
    try:
        with tempfile.TemporaryDirectory() as tempdir:
            yield tempdir
    finally:
        os.chdir(PROJECT_ROOT)  # Ensure that we are returned to the original directory.


def test_synspec(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.run(model)

    # Check that the output files are correct.
    for unit, ext in [
        ("7", "spec"),
        ("12", "iden"),
        ("16", "eqws"),
        ("17", "cont"),
    ]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{tempdir}/fort.{unit}"
        )


@pytest.mark.parametrize(
    "missingfile",
    [
        "fort.19",
        "fort.55",
        "{model}.5",
        "{model}.7",
    ],
)
def test_with_missing_files(missingfile: str, tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]
    files.remove(missingfile)

    _ = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    with pytest.raises(FileNotFoundError):
        synspec.run(model)


def test_synspec_indir(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)
    rundir = f"{tempdir}/run"

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(model, rundir=rundir)

    # Check that the output files are correct.
    for unit, ext in [
        ("7", "spec"),
        ("12", "iden"),
        ("16", "eqws"),
        ("17", "cont"),
    ]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{rundir}/fort.{unit}"
        )


@pytest.mark.parametrize(
    "outdir",
    [
        None,
        "{tempdir}/output",
        "{tempdir}",
    ],
)
def test_synspec_outdir(tempdir: str, outdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)
    if outdir is not None:
        outdir = outdir.format(tempdir=tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.run(model, outdir=outdir)

    # Check that the output files are correct.
    if outdir is None:
        outdir = tempdir
    for ext in ["spec", "iden", "eqws", "cont", "log"]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{outdir}/{model}.{ext}"
        )


def test_synspec_outfilenames(tempdir: str) -> None:
    outfile = "test"
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)
    rundir = f"{tempdir}/run"
    outdir = f"{tempdir}/output"
    os.makedirs(rundir)
    os.makedirs(outdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(model, rundir=rundir, outdir=outdir, outfile=outfile)

    # Check that the output files are correct.
    for ext in ["spec", "log"]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{outdir}/{outfile}.{ext}"
        )


def test_synspec_no_indir(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(model, rundir=None)

    for ext in ["spec", "log"]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{tempdir}/{model}.{ext}"
        )
    for unit in ["7", "12", "16", "17"]:
        assert not os.path.isfile(f"{tempdir}/fort.{unit}")


@pytest.mark.skip(reason="Not implemented yet")
def test_synspec_simultaneous_run(tempdir: str) -> None:
    """This test should try to run two Synspec objects at the same time. The
    expected behaviour is to either raise an exception or to for the second
    wait until the first is finished.
    """
    raise NotImplementedError("This test is not implemented yet.")


def test_synspec_no_model(tempdir: str) -> None:
    """Test that the Synspec object raises an exception if no model is given."""
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    _ = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    with pytest.raises(TypeError):
        synspec.run(None)  # type: ignore


def test_synspec_redirect_files(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)
    os.rename("fort.19", "linelist")

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.add_link("linelist", "fort.19")
    synspec.run(model, rundir=None)

    # Check that the output files are correct.
    assert compare_files(f"{modeldir}/output/{model}.spec", f"{tempdir}/{model}.spec")


def test_synspec_redirect_files_cwd(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)
    os.rename("fort.19", "linelist")

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.add_link("linelist", "fort.19")
    synspec.run(model)

    # Check that the output files are correct.
    assert compare_files(f"{modeldir}/output/{model}.spec", f"{tempdir}/fort.7")


def test_synspec_no_files(tempdir: str) -> None:
    """Test that the Synspec object raises an exception if no files are given."""
    model = "hhe35lt"

    _ = copy_model(model, [], tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    with pytest.raises(FileNotFoundError):
        synspec.run(model)


def test_synspec_autoinclude_fort56(tempdir: str) -> None:
    """Test that the Synspec object automatically includes fort.56 if it is
    required.
    """
    model = "EHeT30g4"
    files = ["fort.19", "fort.55", "fort.56", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.add_link("nst_l")
    synspec.run(model)

    compare_files(f"{modeldir}/output/{model}.spec", f"{tempdir}/fort.7")


def test_synspec_autoinclude_readinput(tempdir: str) -> None:
    """Test that the Synspec object automatically includes the files detected in
    the input file ({model}.5).
    """
    model = "EHeT30g4"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7", "fort.56"]

    modeldir = copy_model(model, files, tempdir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    # Don't explicity add these links
    # synspec.add_link("data")
    # synspec.add_link("nst_l")
    synspec.run(model)

    compare_files(f"{modeldir}/output/{model}.spec", f"{tempdir}/fort.7")


def test_synspec_model_with_dirname(tempdir: str) -> None:
    """Test that the Synspec object can run a model which is in a different
    directory.
    """
    model = "hhe35lt"
    files = ["fort.19", "fort.55"]

    modeldir = copy_model(model, files, tempdir)
    runmoddir = f"{tempdir}/model"
    os.mkdir(runmoddir)
    shutil.copy(f"{modeldir}/input/{model}.5", runmoddir)
    shutil.copy(f"{modeldir}/input/{model}.7", runmoddir)

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(f"model/{model}")

    compare_files(f"{modeldir}/output/{model}.spec", f"{tempdir}/{model}.spec")


def test_synspec_dirmodel_indir(tempdir: str) -> None:
    """Test that the Synspec object can run a model which is in a different
    directory.
    """
    model = "hhe35lt"
    files = ["fort.19", "fort.55"]

    modeldir = copy_model(model, files, tempdir)
    runmoddir = f"{tempdir}/model"
    os.mkdir(runmoddir)
    shutil.copy(f"{modeldir}/input/{model}.5", runmoddir)
    shutil.copy(f"{modeldir}/input/{model}.7", runmoddir)

    rundir = f"{tempdir}/run"

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(f"model/{model}", rundir=rundir)

    compare_files(f"{modeldir}/output/{model}.spec", f"{rundir}/{model}.spec")
    compare_files(f"{modeldir}/input/{model}.5", f"{rundir}/{model}.5")


def test_addlink_relpath(tempdir: str) -> None:
    """Test that the Synspec object can add a link when a relative path exists"""
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)
    rundir = f"{tempdir}/run"

    os.chdir(tempdir)
    os.mkdir(rundir)
    os.symlink("../fort.19", "run/fort.19")

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.add_link("data")
    synspec.run(model, rundir=rundir)

    compare_files(f"{modeldir}/output/{model}.spec", f"{rundir}/{model}.spec")


def test_overwrite_old_files(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)
    shutil.copy(
        f"{modeldir}/output/hhe35lt.cont".format(model=model), f"{tempdir}/fort.7"
    )
    shutil.copy(
        f"{modeldir}/output/hhe35lt.cont".format(model=model),
        f"{tempdir}/hhe35lt.spec",
    )

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    synspec.run(model)

    # Check that the output files are correct.
    outdir = tempdir
    for ext in ["spec", "iden", "eqws", "cont", "log"]:
        assert compare_files(
            f"{modeldir}/output/{model}.{ext}", f"{outdir}/{model}.{ext}"
        )


def test_dont_copy_old_files_on_fail(tempdir: str) -> None:
    model = "hhe35lt"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)
    shutil.copy(
        f"{modeldir}/output/hhe35lt.cont".format(model=model), f"{tempdir}/fort.7"
    )

    # Corrupt input model to make the run fail.
    with open(f"{tempdir}/{model}.7") as f:
        text = f.read()
    with open(f"{tempdir}/{model}.7", "w") as f:
        f.write(text[:-20])

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    try:
        synspec.run(model)

    except subprocess.CalledProcessError:
        # Check that the output files are correct.
        outdir = tempdir
        for ext in ["spec", "iden", "eqws", "cont", "log"]:
            assert not os.path.isfile(f"{outdir}/{model}.{ext}")
    else:
        raise Exception("Process didn't fail despite faulty input files.")


def test_delete_old_output_files_on_fail(tempdir: str) -> None:
    model = "hhe35lt"
    omodel = "EHeT30g4"
    files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]

    modeldir = copy_model(model, files, tempdir)
    for ext in ["spec", "iden", "eqws", "cont", "log"]:
        shutil.copy(
            f"{modeldir}/../{omodel}/output/{omodel}.{ext}", f"{tempdir}/{model}.{ext}"
        )

    # Corrupt input model to make the run fail.
    with open(f"{tempdir}/{model}.7") as f:
        text = f.read()
    with open(f"{tempdir}/{model}.7", "w") as f:
        f.write(text[:-20])

    os.chdir(tempdir)

    # Create a Synspec object.
    synspec = Synspec("synspec", 51)
    try:
        synspec.run(model)

    except subprocess.CalledProcessError:
        # Check that the output files are correct.
        outdir = tempdir
        for ext in ["spec", "iden", "eqws", "cont"]:
            assert not os.path.isfile(f"{outdir}/{model}.{ext}")
    else:
        raise Exception("Process didn't fail despite faulty input files.")

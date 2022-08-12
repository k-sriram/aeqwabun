import functools
import shutil
import subprocess
import tempfile
from contextlib import _GeneratorContextManager, contextmanager
from pathlib import Path
from typing import Callable, Iterator

from aeqwabun.synspec import units, utils


class Synspec:
    def __init__(self, synspecpath: str = "synspec", version: int = 51):
        if version != 51:
            raise NotImplementedError("Only version 51 is supported")
        self.version = version
        self.synspec = synspecpath
        self.linkfiles: dict[str, str | Path] = {  # default links
            "fort.19": "fort.19",
            "fort.55": "fort.55",
            "{model}.5": "{modelpath}.5",
            "{model}.7": "{modelpath}.7",
        }

    def add_link(self, linkfrom: str, linkto: str = None) -> None:
        """Adds a link from the given file to the given file."""
        if linkto is None:
            linkto = linkfrom
        self.linkfiles[linkto] = linkfrom

    def run(
        self,
        model: str,
        rundir: str | Path | None = ".",
        outdir: str | Path | None = None,
        outfile: str | None = None,
    ) -> None:
        """Runs synspec with the given model.
        rundir: directory to run synspec in.
                defaults to running in the current directory.
                if explicitly set to None, a temporary directory is used.
        outdir: directory to copy the output files to.
        outfile: name (without extension) of the output files.
        """
        modelpath = Path(model).resolve()
        model = modelpath.name
        if rundir is None:
            if outdir is None:
                outdir = Path.cwd()
            rdprovider: Callable[[], _GeneratorContextManager[Path]] = tempdir
        else:
            rundir = Path(rundir).resolve()
            rundir.mkdir(exist_ok=True)
            rdprovider = functools.partial(
                utils.folderlock, path=rundir, lockfn="synspec.lock"
            )

        if outdir is None:
            outdir = rundir
        outdir = Path(outdir).resolve()

        if outfile is None:
            outfile = model

        with rdprovider() as rundir:
            self._remove_potential_outfiles(model, outdir, outfile)
            self._copy_to_rundir(model, modelpath, rundir)
            self._check_files(model, rundir)
            self._run(model, rundir)
            self._extract_outfiles(model, rundir, outdir, outfile)

    def _run(self, model: str, rundir: Path) -> None:
        utils.symlinkf(f"{model}.7", rundir / "fort.8")
        with open(rundir / f"{model}.5") as modelinput, open(
            rundir / "fort.log", "w"
        ) as log:
            subprocess.run(
                [self.synspec], stdin=modelinput, stdout=log, cwd=rundir, check=True
            )

    def _extract_outfiles(
        self, model: str, rundir: Path, outdir: Path, outfile: str | None
    ) -> None:
        outdir.mkdir(exist_ok=True)

        for unit, ext in [
            ("7", "spec"),
            ("12", "iden"),
            ("16", "eqws"),
            ("17", "cont"),
        ]:
            shutil.copyfile(rundir / f"fort.{unit}", outdir / f"{outfile}.{ext}")
        shutil.copyfile(rundir / "fort.log", outdir / f"{outfile}.log")

    def _remove_potential_outfiles(
        self, model: str, outdir: Path, outfile: str | None
    ) -> None:
        if not outdir.is_dir():
            return
        for ext in ["spec", "iden", "eqws", "cont"]:
            f = outdir / f"{outfile}.{ext}"
            print(f"Should delete {f}")
            if f.is_file():
                f.unlink()

    def _copy_to_rundir(self, model: str, modelpath: Path, rundir: Path) -> None:
        # Read the input file to see if extra links are required.
        inputfile = str(self.linkfiles["{model}.5"]).format(
            model=model, modelpath=modelpath
        )
        with open(inputfile) as f:
            modelinput = units.readinput(f.read())
        reqs = []
        if modelinput.get("finstd"):
            reqs.append(modelinput["finstd"])
        if "ions" in modelinput:
            for ion in modelinput["ions"]:
                reqs.append(ion["filei"])
        reqs = list(
            {
                str(x).split("/", maxsplit=1)[0]
                for x in map(Path, reqs)
                if not x.is_absolute()
            }
        )

        for req in reqs:
            if Path(req).exists() and req not in self.linkfiles:
                self.linkfiles[req] = req

        # Detect need for fort.56
        if "fort.56" not in self.linkfiles:
            cofigfile = Path(str(self.linkfiles["fort.55"]).format(model=model))
            config = units.read55f(cofigfile)
            if config.ichemc != 0:
                if Path("fort.56").is_file():
                    self.linkfiles["fort.56"] = "fort.56"
                else:
                    raise FileNotFoundError("Need for fort.56 detected but not found")

        # Link the required files to the run directory.
        for dst, src in self.linkfiles.items():
            src = Path(str(src).format(model=model, modelpath=modelpath)).resolve()
            if (
                rundir != Path.cwd().resolve()
                or src
                != Path(str(dst).format(model=model, modelpath=modelpath)).resolve()
            ):
                utils.symlinkf(
                    src, rundir / dst.format(model=model, modelpath=modelpath)
                )

    def _check_files(self, model: str, rundir: Path) -> None:
        """Checks if the required files exist."""
        files = ["fort.19", "fort.55", "{model}.5", "{model}.7"]
        for file in files:
            if not Path(fn := rundir / file.format(model=model)).exists():
                raise FileNotFoundError(f"{fn} not found")


@contextmanager
def tempdir() -> Iterator[Path]:
    """Context manager for temporary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir).resolve()

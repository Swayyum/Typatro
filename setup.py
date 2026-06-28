from pathlib import Path

from setuptools import setup
from setuptools.command.editable_wheel import editable_wheel as _EditableWheel

ROOT = Path(__file__).resolve().parent
EDITABLE_PTH = "typatro-editable-root.pth"


class EditableWheel(_EditableWheel):
    """Write a non-hidden .pth so Python 3.12+ loads editable project roots."""

    def _install_editable_pth(self, lib_dir: str, pth_name: str) -> None:
        super()._install_editable_pth(lib_dir, pth_name)
        pth_path = Path(lib_dir) / EDITABLE_PTH
        pth_path.write_text(f"{ROOT}\n", encoding="utf-8")


setup(cmdclass={"editable_wheel": EditableWheel})

import os
import shutil
import subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install

def compile_and_copy_tgrep2():
    """
    Compiles both refactored versions of tgrep2 and copies the binaries
    to the pytgrep2/bin package directory to bundle them, as well as copying
    the default variant to $HOME/.local/bin.
    """
    base_dir = Path(__file__).parent.resolve()
    andreas_dir = base_dir / "tgrep2-andreasvc-refactored"
    bwaldon_dir = base_dir / "tgrep2-bwaldon-refactored"
    
    print("--------------------------------------------------")
    print("Compiling tgrep2 binaries...")
    print("--------------------------------------------------")
    
    # 1. Compile tgrep2-andreasvc
    try:
        subprocess.check_call(["make", "-C", str(andreas_dir / "DRUtils"), "clean"])
        subprocess.check_call(["make", "-C", str(andreas_dir / "TGrep2"), "clean"])
        subprocess.check_call(["make", "-C", str(andreas_dir / "DRUtils")])
        subprocess.check_call(["make", "-C", str(andreas_dir / "TGrep2")])
    except subprocess.CalledProcessError as e:
        print(f"ERROR: andreasvc compilation failed: {e}")
        raise RuntimeError("Failed to compile tgrep2-andreasvc C binary.") from e

    # 2. Compile tgrep2-bwaldon
    try:
        subprocess.check_call(["make", "-C", str(bwaldon_dir), "clean"])
        subprocess.check_call(["make", "-C", str(bwaldon_dir), "tgrep2"])
    except subprocess.CalledProcessError as e:
        print(f"ERROR: bwaldon compilation failed: {e}")
        raise RuntimeError("Failed to compile tgrep2-bwaldon C binary.") from e

    # Create destination bin directory within the python package folder
    package_bin_dir = base_dir / "pytgrep2" / "bin"
    package_bin_dir.mkdir(parents=True, exist_ok=True)

    andreas_dest = package_bin_dir / "tgrep2-andreasvc"
    bwaldon_dest = package_bin_dir / "tgrep2-bwaldon"

    print(f"Copying compiled binaries to package bin folder: {package_bin_dir}")
    shutil.copy2(andreas_dir / "tgrep2", andreas_dest)
    shutil.copy2(bwaldon_dir / "tgrep2", bwaldon_dest)

    andreas_dest.chmod(0o755)
    bwaldon_dest.chmod(0o755)

    # Copy to root bin/ directory for local tests and programs
    root_bin_dir = base_dir / "bin"
    root_bin_dir.mkdir(parents=True, exist_ok=True)
    
    root_andreas_dest = root_bin_dir / "tgrep2-andreasvc"
    root_bwaldon_dest = root_bin_dir / "tgrep2-bwaldon"
    
    print(f"Copying compiled binaries to root bin folder: {root_bin_dir}")
    shutil.copy2(andreas_dir / "tgrep2", root_andreas_dest)
    shutil.copy2(bwaldon_dir / "tgrep2", root_bwaldon_dest)
    
    root_andreas_dest.chmod(0o755)
    root_bwaldon_dest.chmod(0o755)

    # 3. Optional copy of the default binary to $HOME/.local/bin for command-line usage
    try:
        dest_dir = Path.home() / ".local" / "bin"
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy as 'tgrep2'
        dest_file = dest_dir / "tgrep2"
        print(f"Copying default binary to: {dest_file}")
        shutil.copy2(andreas_dir / "tgrep2", dest_file)
        dest_file.chmod(0o755)
        
        print("tgrep2 installation to $HOME/.local/bin completed.")
    except Exception as e:
        print(f"Warning: Could not copy default binary to $HOME/.local/bin: {e}")
        
    print("--------------------------------------------------")

class CustomBuildPy(build_py):
    def run(self):
        compile_and_copy_tgrep2()
        super().run()

class CustomDevelop(develop):
    def run(self):
        compile_and_copy_tgrep2()
        super().run()

class CustomInstall(install):
    def run(self):
        compile_and_copy_tgrep2()
        super().run()

setup(
    name="pytgrep2",
    version="1.0.0",
    description="Python linguistic analysis pipeline coordinating constituency parsing, corpus indexing, and structural searches using tgrep2",
    author="Andrew Ernest Ritz",
    packages=["pytgrep2"],
    package_data={
        "pytgrep2": ["bin/tgrep2-andreasvc", "bin/tgrep2-bwaldon"],
    },
    install_requires=[
        "spacy>=3.0.0",
        "benepar @ git+https://github.com/drewvid/self-attentive-parser.git",
        "nltk>=3.0.0",
        "google-genai",
        "compress-pickle",
    ],
    cmdclass={
        'build_py': CustomBuildPy,
        'develop': CustomDevelop,
        'install': CustomInstall,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
)

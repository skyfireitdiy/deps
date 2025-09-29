#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import shutil
from pathlib import Path
import typer
from typing_extensions import Annotated


def get_deps(elf):
    output = subprocess.check_output(f"ldd {elf}", shell=True).decode()
    ld = ""
    libs = {}
    for line in output.splitlines():
        if "ld-linux" in line:
            ld = line.split()[0]
        elif "=>" in line:
            cols = line.split("=>")
            target = cols[1].split("(")[0].strip()
            libs[cols[0].strip()] = target
    return (ld, libs)


def resolve_deps(elf, deps, work_dir):
    libs = deps[1]
    lib_dir = os.path.join(work_dir, "lib")
    print(f"mkdir {lib_dir}")
    os.makedirs(lib_dir, exist_ok=True)
    for k, v in libs.items():
        realpath = os.path.realpath(v)
        if realpath == "":
            print(v, "not found!")
            sys.exit(0)

        print(f"copy {realpath} => {os.path.join(lib_dir, k)}")
        shutil.copy(realpath, os.path.join(lib_dir, k))
    loader_name = os.path.basename(deps[0])
    loader_path = os.path.join(lib_dir, loader_name)
    print(f"copy {deps[0]} => {loader_path}")
    shutil.copy(deps[0], loader_path)

    elf_name = os.path.basename(elf)
    if shutil.which("patchelf"):
        elf_path = os.path.join(work_dir, elf_name)
        print(f"copy {elf} => {elf_path}")
        shutil.copy(elf, elf_path)
        os.chmod(elf_path, 0o755)

        print("patchelf found, patching elf in-place")
        subprocess.run(
            ["patchelf", "--set-interpreter",
                f"lib/{loader_name}", elf_path],
            check=True)
        subprocess.run(
            ["patchelf", "--set-rpath", "$ORIGIN/lib", elf_path],
            check=True)
    else:
        print("warning: 'patchelf' not found. Creating a wrapper script.")
        print("warning: The executable may not be portable to systems without the exact library paths.")
        bin_dir = os.path.join(work_dir, "bin")
        print(f"mkdir {bin_dir}")
        os.makedirs(bin_dir, exist_ok=True)
        elf_path = os.path.join(bin_dir, elf_name)
        print(f"copy {elf} => {elf_path}")
        shutil.copy(elf, elf_path)

        start_script = os.path.join(work_dir, elf_name)
        print(f"write start script to {start_script}")
        with open(start_script, "w") as fp:
            fp.write(
                f'''#!/bin/bash
DIR=$(dirname $(realpath $0))
$DIR/lib/{loader_name} --library-path $DIR/lib $DIR/bin/{elf_name} $*
''')
        os.chmod(start_script, 0o755)

app = typer.Typer()

@app.command()
def main(
    elf_path: Annotated[str, typer.Argument(help="The ELF executable to process.")],
    directory: Annotated[Path, typer.Option("-d", "--directory", help="The output directory for the packaged application.", rich_help_panel="Customization and Utils")],
):
    """
    Finds all shared library dependencies for an ELF executable,
    copies them into a deployable directory structure, and creates a launcher.
    """
    try:
        elf = subprocess.check_output(
            f"which {elf_path}", shell=True).decode().strip()
    except subprocess.CalledProcessError:
        elf = ""
        
    if not elf:
        print(f"Error: Executable '{elf_path}' not found in PATH.")
        raise typer.Exit(code=1)
        
    print(f"Processing '{elf}'...")
    deps = get_deps(elf)
    resolve_deps(elf, deps, str(directory))
    print("Finished!")


if __name__ == "__main__":
    app()

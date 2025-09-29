#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
import os
import shutil


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

    bin_dir = os.path.join(work_dir, "bin")
    print(f"mkdir {bin_dir}")
    os.makedirs(bin_dir, exist_ok=True)
    elf_name = os.path.basename(elf)
    elf_path = os.path.join(bin_dir, elf_name)
    print(f"copy {elf} => {elf_path}")
    shutil.copy(elf, elf_path)

    if shutil.which("patchelf"):
        print("patchelf found, patching elf")
        subprocess.run(
            ["patchelf", "--set-interpreter",
                f"../lib/{loader_name}", elf_path],
            check=True)
        subprocess.run(
            ["patchelf", "--set-rpath", "$ORIGIN/../lib", elf_path],
            check=True)

        start_script = os.path.join(work_dir, elf_name)
        if os.path.lexists(start_script):
            os.remove(start_script)
        os.symlink(f"bin/{elf_name}", start_script)
        print(f"create symlink {start_script} -> bin/{elf_name}")
    else:
        start_script = os.path.join(work_dir, elf_name)
        print(f"write start script to {start_script}")
        with open(start_script, "w") as fp:
            fp.write(
                f'''#!/bin/bash
DIR=$(dirname $(realpath $0))
$DIR/lib/{loader_name} --library-path $DIR/lib $DIR/bin/{elf_name} $*
''')
        os.chmod(start_script, 0o755)

def main():
    parser = argparse.ArgumentParser("deps")
    parser.add_argument("elf_path")
    parser.add_argument("-d", "--directory", required=True, help="工作路径")
    result = parser.parse_args()
    elf = subprocess.check_output(
        "which " + result.elf_path, shell=True).decode().strip()
    if not elf:
        print(f"{elf} not found!")
        exit()
    deps = get_deps(elf)
    resolve_deps(elf, deps, result.directory)
    print("finished")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
import os
import shutil


def get_deps(elf):
    output = subprocess.check_output("ldd " + elf, shell=True).decode()
    ld = ""
    libs = {}
    for line in output.splitlines():
        if "=>" in line:
            cols = line.split("=>")
            target = cols[1].split("(")[0].strip()
            libs[cols[0].strip()] = target
        elif "ld-linux" in line:
            ld = line.split()[0]
    return (ld, libs)


def resolve_deps(elf, deps, work_dir):
    libs = deps[1]
    lib_dir = os.path.join(work_dir, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    for k, v in libs.items():
        realpath = os.path.realpath(v)
        if realpath == "":
            print(v, "not found!")
            sys.exit(0)
        shutil.copy(realpath, os.path.join(lib_dir, k))
    loader_name = os.path.basename(deps[0])
    loader_path = os.path.join(lib_dir, loader_name)
    shutil.copy(deps[0], loader_path)

    bin_dir = os.path.join(work_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    elf_name = os.path.basename(elf)
    shutil.copy(elf, os.path.join(bin_dir, elf_name))
    start_script = os.path.join(work_dir, elf_name)

    with open(start_script, "w") as fp:
        fp.write(
            '''#!/bin/bash
DIR=$(dirname $(realpath $0))
$DIR/lib/%s --library-path $DIR/lib $DIR/bin/%s $*
''' % (loader_name, elf_name)
        )
    os.chmod(start_script, 0o755)


def main():
    parser = argparse.ArgumentParser("deps")
    parser.add_argument("elf_path")
    parser.add_argument("-d", "--directory", required=True, help="工作路径")
    result = parser.parse_args()
    deps = get_deps(result.elf_path)
    resolve_deps(result.elf_path, deps, result.directory)


if __name__ == "__main__":
    main()

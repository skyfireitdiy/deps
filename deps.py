#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
import os
import shutil
from unittest import loader


def get_deps(elf):
    output = subprocess.check_output("ldd " + elf, shell=True).decode()
    r = re.compile(r'''([\w.\-\d/]+)\s*(=>)?\s*([\w.\-\d/]+)*\s+\(.*\)''')
    result = r.findall(output)
    libs = {}
    ld = ""
    for r in result:
        if "vdso.so" in r[0]:
            continue
        if "ld-linux-" in r[0]:
            ld = r[0]
            continue
        if r[2] == "":
            print(r[0], "not found!")
            sys.exit(0)
        libs[r[0]] = r[2]
    return (ld, libs)


def resolve_deps(elf, deps, workdir):
    libs = deps[1]
    libdir = os.path.join(workdir, "lib")
    os.makedirs(libdir, exist_ok=True)
    for k, v in libs.items():
        realpath = os.path.realpath(v)
        if realpath == "":
            print(v, "not found!")
            sys.exit(0)
        shutil.copy(realpath, os.path.join(libdir, k))
    loader_name = os.path.basename(deps[0])
    loader_path = os.path.join(libdir, loader_name)
    shutil.copy(deps[0], loader_path)

    bindir = os.path.join(workdir, "bin")
    os.makedirs(bindir, exist_ok=True)
    elfname = os.path.basename(elf)
    shutil.copy(elf, os.path.join(bindir, elfname))

    with open(os.path.join(workdir, elfname), "w") as fp:
        fp.write(
            '''#!/bin/bash
DIR=$0
get_real(){
 if [ -h $DIR ]; then
  DIR=$(readlink $DIR)
  get_real
 else
  DIR=$(dirname $DIR)
 fi
}

get_real

$DIR/lib/%s --library-path $DIR/lib $DIR/bin/%s $*
''' % (loader_name, elfname)
        )


def main():
    parser = argparse.ArgumentParser("deps")
    parser.add_argument("elfpath")
    parser.add_argument("-d", "--directory", required=True, help="工作路径")
    result = parser.parse_args()
    deps = get_deps(result.elfpath)
    resolve_deps(result.elfpath, deps, result.directory)


if __name__ == "__main__":
    main()

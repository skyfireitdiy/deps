[中文](./README_zh.md)

# Deps Resolver

A simple command-line tool to find all shared library dependencies for an ELF executable, copy them into a deployable directory structure, and create a launcher. 

It can use `patchelf` to modify the ELF interpreter and rpath for a cleaner setup, or fall back to a wrapper script if `patchelf` is not available.

## Installation

You can install the package directly from the source code:

```bash
pip install .
```

## Usage

The tool `deps` takes two arguments: the name of an ELF executable and a directory to place the packaged application.

```bash
deps <executable_name> -d <output_directory>
```

### Example

Let's say you want to package the `ls` command:

```bash
deps ls -d /tmp/ls_package
```

This will create a directory `/tmp/ls_package`.

If `patchelf` is available on your system, the structure will be:
```
/tmp/ls_package/
├── lib/
│   ├── libc.so.6
│   ├── ld-linux-x86-64.so.2
│   └── ...     # Other dependencies
└── ls          # The patched executable
```

If `patchelf` is not found, it will fall back to using a wrapper script, and the structure will be:
```
/tmp/ls_package/
├── bin/
│   └── ls      # The original executable
├── lib/
│   ├── libc.so.6
│   ├── ld-linux-x86-64.so.2
│   └── ...     # Other dependencies
└── ls          # A launcher script that calls the executable in bin/
```

You can then run the packaged application by executing the launcher:

```bash
/tmp/ls_package/ls
```

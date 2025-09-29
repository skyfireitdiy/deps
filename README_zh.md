[English](./README.md)

# Deps Resolver (依赖解析器)

一个简单的命令行工具，用于查找 ELF 可执行文件的所有共享库依赖，并将它们复制到一个可部署的目录结构中，同时创建一个启动器。

它可以使用 `patchelf` 来修改 ELF 解释器和 rpath 以实现更清晰的部署，如果 `patchelf` 不可用，则会回退到使用包装脚本的方式。

## 安装

您可以直接从源代码安装本工具：

```bash
pip install .
```

## 使用方法

`deps` 工具接受两个参数：一个 ELF 可执行文件的名称和一个用于存放打包后应用的目录。

```bash
deps <executable_name> -d <output_directory>
```

### 示例

假设您想要打包 `ls` 命令：

```bash
deps ls -d /tmp/ls_package
```

这将在 `/tmp/ls_package` 目录下创建应用包。

如果您的系统上存在 `patchelf`，目录结构会是这样：
```
/tmp/ls_package/
├── lib/
│   ├── libc.so.6
│   ├── ld-linux-x86-64.so.2
│   └── ...     # 其他依赖库
└── ls          # 已被 patchelf 修改的可执行文件
```

如果未找到 `patchelf`，工具会回退到使用包装脚本，目录结构会是这样：
```
/tmp/ls_package/
├── bin/
│   └── ls      # 原始可执行文件
├── lib/
│   ├── libc.so.6
│   ├── ld-linux-x86-64.so.2
│   └── ...     # 其他依赖库
└── ls          # 调用 bin/ 目录下可执行文件的启动脚本
```

您可以通过执行启动器来运行打包好的应用：

```bash
/tmp/ls_package/ls
```

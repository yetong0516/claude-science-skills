# Claude Science Skills

A versioned, unofficial export of locally readable Claude Science skill definitions.

## 当前快照：0.1.70

2026-10-26 核对本机已暂存的 `0.1.70-release` 运行时后更新。保留 **29 个 skill 包**，同步 **30 个已有文件**的变化（其中 **15 份 SKILL.md**），新增 `THIRD_PARTY_LICENSES.md`。共 **81 个导出文件**，逐文件记录 SHA-256；原仓库的 29 个 `.catalog_stamp` 标记保留为历史文件，不算入本次快照。

- [本次更新及使用边界](docs/updates/2026-10-26-0.1.70.md)
- [文件哈希与来源记录](SNAPSHOT.json) · [完整变更清单](docs/updates/0.1.70-files.json)
- [本地随附的 24 组 MCP 服务目录](catalogs/bundled-mcp.json) · [如何理解这份目录](docs/mcp-inventory.md)

MCP 目录仅记录安装包中的服务分组及入口文件哈希，未包含服务实现、账号配置或数据库，也未测试服务连接。29 个本地包、24 组服务与官方产品的整体功能数量属于不同统计口径，不能互相替代。本仓库不声称恢复了完整平台。

## 中文声明

本仓库是从本地 Claude Science 安装目录导出的 skill 定义备份，主要用于个人学习、研究工作流整理和版本保存。仓库内容不代表 Claude Science 官方发布，也不构成 Anthropic 或任何上游项目的授权、背书或服务承诺。

本次导出的内容包括 `skills/` 目录中的 skill 文档、参考资料和随附脚本，以及仓库维护的版本记录、校验工具和脱敏 MCP 目录。不包含 Claude Science 的运行时数据、组织数据、用户数据、病例/影像数据、conda 环境、数据库、登录状态、访问令牌、API 密钥或其他凭据。

仓库中的部分 skill 可能引用第三方模型、软件包、远程计算平台、数据服务或 API。使用这些功能前，请自行确认相应的开源许可证、版权要求、服务条款、商业使用限制和数据合规要求。将本仓库公开不改变任何上游项目或第三方材料原有的权利归属和许可条件。

如果你要基于这些 skill 进行再分发、修改或商业使用，请先逐项核对相关上游许可。当前快照保留新增的 [第三方许可声明](skills/THIRD_PARTY_LICENSES.md) 和各 skill 的原始声明；这些声明不构成覆盖全部仓库内容的统一授权。

## 使用与验证

先阅读所需包的 `SKILL.md`，再核对计算环境、模型权重、依赖和服务权限。涉及 `host.*`、`repl`、组织设置、远程计算或托管模型的说明依赖 Claude Science 宿主；直接复制到其他 agent 环境并不能补齐这些接口，需要另行适配。本次更新保留原始内容，没有把宿主调用改写成未经验证的替代实现。

在仓库根目录使用 Python 3.12 执行：

```sh
python3 scripts/verify_snapshot.py
python3 -m unittest discover -s tests -v
```

校验覆盖导出文件的大小/哈希、缺失/多余文件、符号链接、包数量、基础 frontmatter、Python 语法和目录元数据。它不会安装依赖、执行 skill、连接数据库或提交计算任务；通过校验不代表科学结果或平台集成已通过验证。

## Contents

The `skills/` directory contains 29 skill packages, including scientific literature review, figure composition, remote compute setup, protein structure and design tools, single-cell analysis, and skill authoring utilities.

This repository also includes snapshot provenance, integrity checks, and a metadata-only inventory of 24 bundled MCP server groups. Server implementations and account-specific connector configuration are not exported.

## Provenance

The original export came from `~/.claude-science/skills`. The current snapshot comes from the locally staged `runtime/0.1.70-release/skills` tree. All 81 exported files match that source byte-for-byte. The official macOS distribution was independently inspected for version 0.1.70 without launching or installing the application; this does not establish that its entire runtime matches the staged tree.

No repository-wide license grant was found. Preserve and check the upstream notices before redistributing or modifying these materials. The third-party notice added in this snapshot does not relicense the export.

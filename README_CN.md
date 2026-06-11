# Token Efficiency Skill - Token 效率优化 Skill

## 这是什么？

**Token Efficiency Skill** 是一个专为 **AI Agent**（智能体）设计的效率优化工具包。

AI Agent 在处理复杂任务时存在一个严重问题：Token 的惊人浪费。真实数据显示真正与当前任务相关的信息只占 10%-20%，其余 80%-90% 都是重复读取、历史回放和无效分析。这个 Skill 就是为此而生。

## 解决的问题

反复读取相同文件、历史对话越滚越大、每轮重新扫描、对已解决问题反复纠结、杀鸡用牛刀式读取、任务完成还在跑 -- 全部解决。

## 适用于哪些 Agent？

所有基于 LLM 且支持 Skill/Plugin 机制的 AI Agent：**Codex**（首选）、**Claude**、**Cursor**、**Windsurf**、**Cline**，以及任何能加载 Markdown 指令文件的 Agent。

原理是一套行为规范加辅助脚本，不依赖特定平台 API。

## 10 大核心能力

1. 历史压缩 - 理解后不再重读原文，用摘要替代。
2. 文件缓存 - 记录哈希和摘要，未变更文件跳过。
3. 增量分析 - 只分析新增、修改、任务相关文件。
4. 上下文裁剪 - 丢弃已完成任务和失效讨论。
5. 循环检测 - 3 轮相同结论即停止分析。
6. 读取预算 - 每轮上限 10 文件/5000 行/50 KB。
7. 上下文记忆 - 记录项目结构、已完成任务、已知结论。
8. 行动优先 - 执行 > 搜索 > 缓存 > 摘要 > 全量读取。
9. 成本感知 - 大操作前估算成本，自动降级。
10. 停止条件 - 达标即停。

## 核心原则

每个 Token 都必须创造价值。禁止重复读取、推理、总结、扫描。优先级：缓存 -> 摘要 -> 增量 -> 执行。

## 安装方法

### Git Clone
```
git clone https://github.com/cheche089/token-efficiency-skill.git
```

macOS / Linux：
```
cp -r token-efficiency-skill ~/.codex/skills/token-efficiency
```

Windows（PowerShell）：
```
Copy-Item -Path ".\token-efficiency-skill\" -Destination "$env:USERPROFILE\.codex\skills\token-efficiency" -Recurse -Force
```

### 手动下载
1. 访问 https://github.com/cheche089/token-efficiency-skill
2. Code -> Download ZIP -> 解压后复制到 Skills 目录

### 验证安装
```
~/.codex/skills/token-efficiency/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/
```

## 使用方式

提示词中引用：$token-efficiency 帮我分析项目结构。

或者处理长期多步任务时自动触发。

## 文件结构

```
token-efficiency/
  SKILL.md              - 核心协议
  README_CN.md          - 本文件（中文说明）
  agents/openai.yaml    - 元数据
  references/           - 3 个参考文件
  scripts/              - 3 个辅助脚本
```

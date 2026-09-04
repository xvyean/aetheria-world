# 版本管理说明

## 为什么拆分

仓库的 v1、v2、v3 原本是一条连续演进历史。v3 之后出现了多套基于同一原版的 AI 重构：一套改写为《余光未尽》并使用船岛 GLB，另一套保留经典世界观并建立 Blender 4.2 / Draco 学院。后来又有一套“设定圣经 + 现代页面”被直接叠加到 `main`，README 和 `.gitignore` 的冲突标记因此被提交。

这次整理不改写旧提交，也不丢弃任何资产。每个可辨认版本都由独立分支指向，`main` 只继续承载已经整理、验证过的综合版。

## 版本谱系

```text
v1 original (f92382c)
└─ v2 expanded world (28e59a8)
   └─ v3 three continents (1e34911)
      ├─ v4 afterglow (b43fde1)
      │  └─ version/v4-modern-bible（v4 综合版快照）
      │      └─ main ── v5 综合版（当前：设定圣经 v5 + Blender 分区管线 + 学院手册页 + 世界舆图页）
      └─ v4 blender academy (7ac41da)
```

## 怎么选

- 想看最初创意：`version/v1-original`
- 想保留较轻量的大陆地图：`version/v2-expanded-world`
- 想要原经典世界观与学院插图：`version/v3-three-continents`
- 想要《余光未尽》设定：`version/v4-afterglow`
- 想要完整的 Blender 4.2 程序化学院和 Draco 模型：`version/v4-blender-academy`
- 想同时保留大陆页与现代学院页：`version/v4-modern-bible`（v5 之前的 main 状态）
- 想要当前 v5 综合版（设计宪法 + 九卷圣经、Blender 分区管线、`academy.html` 学院手册、`world-modern.html` 世界舆图）：`main`

## 恢复与比较

```bash
# 临时查看一个版本，不改当前分支
git switch --detach version/v3-three-continents

# 回到默认版本
git switch main

# 比较两套 v4 的文件差异
git diff --stat version/v4-afterglow..version/v4-blender-academy
```

## 后续 AI 协作约定

1. 先明确基线分支，再创建 `variant/<方案名>`。
2. 一个分支只承载一种创作方向。
3. 合并前检查冲突标记、JavaScript 语法和本地资源引用。
4. 创意冲突不能通过同时保留两侧文本来“解决”。需要双版本时保留两个分支。
5. `main` 只接收用户明确选中的方案或经过验证的整合。


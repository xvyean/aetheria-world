<div align="center">

# 艾瑟兰 Aetheria

**三块大陆 · 星槎学院 · 多版本世界构建**

`Three.js` · `Blender` · `程序化大陆` · `高奇幻设定`

</div>

---

## 默认版本

`main` 是当前整理后的综合版本，保留两种互不覆盖的入口：

- `index.html`：三维大陆与《余光未尽》星槎学院。
- `world-modern.html`：设定圣经驱动的现代学院观察器。

两套入口共享必要资产，但各自拥有独立页面和渲染代码。README 与 `.gitignore` 中误提交的 Git 冲突标记已经清除。

## 版本分支

不同 AI 产生的创作路线不再相互覆盖，而是保存在独立分支中：

| 分支 | 内容 | 基线 |
| --- | --- | --- |
| [`version/v1-original`](https://github.com/xvyean/aetheria-world/tree/version/v1-original) | 最初的单大陆 3D 奇幻世界 | `f92382c` |
| [`version/v2-expanded-world`](https://github.com/xvyean/aetheria-world/tree/version/v2-expanded-world) | 三河两湖、十四势力的大陆级扩展 | `28e59a8` |
| [`version/v3-three-continents`](https://github.com/xvyean/aetheria-world/tree/version/v3-three-continents) | 三块大陆、四十二城、初版星槎学院 | `1e34911` |
| [`version/v4-afterglow`](https://github.com/xvyean/aetheria-world/tree/version/v4-afterglow) | 《余光未尽》设定与船岛 GLB | `b43fde1` |
| [`version/v4-blender-academy`](https://github.com/xvyean/aetheria-world/tree/version/v4-blender-academy) | 独立 Blender 4.2 / Draco 学院方案 | `7ac41da` |
| [`version/v4-modern-bible`](https://github.com/xvyean/aetheria-world/tree/version/v4-modern-bible) | 当前综合版的固定快照 | 见该分支最新提交 |

完整的分支来源、选择建议和恢复方法见 [`VERSIONING.md`](VERSIONING.md)。

## 本地运行

本项目无需构建。由于 GLB 通过 `fetch` 加载，请从项目根目录启动静态服务器：

```bash
python -m http.server 8080
```

然后访问：

- <http://localhost:8080/>：默认三维世界。
- <http://localhost:8080/world-modern.html>：现代学院观察器。

Three.js、OrbitControls 与 GLTFLoader 已放在 `vendor/`，浏览页面不需要安装 npm 依赖。

## 选择或创建版本

```bash
# 查看所有版本
git branch --all

# 切换到一个已有版本
git switch version/v3-three-continents

# 从指定基线创建新的 AI 方案
git switch version/v3-three-continents
git switch -c variant/my-new-direction
```

新的 AI 修改应始终进入 `variant/*` 或单独的功能分支；确认方向后再合并到 `main`。不要把两个版本的冲突段落同时保留。

## 许可

[MIT License](LICENSE)

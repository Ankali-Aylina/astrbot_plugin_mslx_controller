<div align="center">
  <img src="logo.png" alt="MSLX Bot Logo" width="128" height="128" />
  <h1>astrbot_plugin_mslxbot</h1>
  <p><strong>MSLX 开服器控制面板 · AstrBot 插件</strong></p>
  <p>
    <a href="https://github.com/Ankali-Aylina/astrbot_plugin_mslxbot">
      <img src="https://img.shields.io/badge/GitHub-Repo-blue?logo=github" alt="GitHub" />
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-AGPLv3-green" alt="License" />
    </a>
    <a href="https://github.com/AstrBotDevs/AstrBot">
      <img src="https://img.shields.io/badge/AstrBot-%3E%3D4.16-orange" alt="AstrBot" />
    </a>
  </p>
</div>

---

## 📖 简介

[`astrbot_plugin_mslx_controller`](main.py) 是一个基于 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 框架的插件，通过调用 [MSLX](https://github.com/MSLTeam/MSLX) 后端 API，在即时通讯平台（如 QQ）上实现对 MSLX 服务器实例和 FRP 隧道的远程控制。

> 你可以在聊天中直接发送指令，完成启动/停止/重启服务器、查看隧道状态等操作，无需登录管理面板。

---

## ✨ 功能特性

### 🖥️ 服务器实例控制

| 指令 | 说明 |
|------|------|
| `/服务器列表` | 查看所有服务器实例及其运行状态 |
| `/启动服务器 <实例ID>` | 启动指定服务器实例 |
| `/停止服务器 <实例ID>` | 停止指定服务器实例 |
| `/重启服务器 <实例ID>` | 重启指定服务器实例 |

### 🔗 FRP 隧道控制

| 指令 | 说明 |
|------|------|
| `/隧道列表` | 查看所有 FRP 隧道及其运行状态 |
| `/隧道详情 <隧道ID>` | 查看指定隧道的代理详情（本地地址 → 远程地址） |
| `/启动隧道 <隧道ID>` | 启动指定隧道 |
| `/停止隧道 <隧道ID>` | 停止指定隧道 |
| `/重启隧道 <隧道ID>` | 重启指定隧道（先停止，等待 1 秒后启动） |

---

## 📦 安装

### 方法一：AstrBot 市场（推荐）

在 AstrBot 管理面板的 **插件市场** 中搜索 `mslxbot` 并安装。

### 方法二：手动安装

1. 进入 AstrBot 的 `plugins` 目录：

```bash
cd /path/to/astrbot/plugins
```

2. 克隆本仓库：

```bash
git clone https://github.com/Ankali-Aylina/astrbot_plugin_mslx_controller.git
```

3. 安装依赖：

```bash
pip install -r astrbot_plugin_mslx_controller/requirements.txt
```

4. 重启 AstrBot。

---

## ⚙️ 配置

在 AstrBot 管理面板的插件配置中，填写以下参数：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `mslx_api.api_root` | `string` | `http://localhost:1027` | MSLX 后端 API 的基础 URL |
| `mslx_api.api_token` | `string` | `""` | MSLX 的 API Key（必填），通过 `x-api-key` Header 传递 |

配置结构如下（[`_conf_schema.json`](_conf_schema.json)）：

```json
{
  "mslx_api": {
    "api_root": "http://localhost:1027",
    "api_token": "your_api_key_here"
  }
}
```

> ⚠️ **注意**：`api_token` 为必填项，未配置时插件会发出警告，且部分功能不可用。该值通过 HTTP Header `x-api-key` 传递给 MSLX 后端进行认证。

---

## 🚀 使用示例

```
/服务器列表
📋 当前服务器实例列表:
1. [1] 我的世界服务器 - 🟢 运行中 (核心: Paper)
2. [2] 模组服 - 🔴 已停止 (核心: Forge)

/启动服务器 1
✅ 服务器实例 `1` 启动指令已发送。
操作成功

/隧道列表
🔗 当前隧道列表:
1. [1] 生存服映射 - 🟢 运行中 (服务: mc, 配置: TCP)

/隧道详情 1
隧道 ID 1 详情 - 🟢 运行中
代理列表:
- mc-server [TCP]: 本地 127.0.0.1:25565 → 远程 example.com:30000 (备用 无)
```

---

## 🧩 依赖

- [`httpx`](requirements.txt) — 异步 HTTP 客户端，用于调用 MSLX API

---

## 📄 许可证

本项目基于 **GNU Affero General Public License v3.0** 开源，详见 [`LICENSE`](LICENSE)。

---

## 🙏 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 强大的聊天机器人框架
- [MSLX](https://github.com/MSLTeam/MSLX) — 开服器管理后端

# Retro Game Store 安装指南

这是一个为复古游戏系统定制的扩展程序。安装后，系统菜单将新增一个 **Game Store** 选项。通过该选项进入 NES 专区，你可以浏览并下载一万多款经典的 NES 游戏。下载完成后，游戏会自动安装至模拟器的相应分类下。

---

## 🚀 核心功能
* **无缝集成**：在系统界面中直接构建 Game Store 入口。
* **海量资源**：支持一键获取 10,000+ 款 NES 复古游戏。
* **自动部署**：游戏下载后自动配置到模拟器路径，无需手动搬运。

---

## 🛠️ 安装方法

### 方法一：一键安装（推荐）
请确保你的系统已联网，并在终端（Terminal/SSH）中执行以下命令：

```bash
curl -L [https://raw.githubusercontent.com/jamssismy/gamestore/main/install.sh](https://raw.githubusercontent.com/jamssismy/gamestore/main/install.sh) | bash
```bash

方法二：手动安装
下载并解压：下载完整程序压缩包。

1.配置文件：将 es_systems_gamestore.cfg 放入以下路径： /userdata/system/configs/emulationstation/

2.创建目录：在 /userdata/roms/ 内新建 gamestore 文件夹。

3.放置资源：将解压包内的 NES 文件夹放入： /userdata/roms/gamestore/

4.更新列表：返回系统界面，执行 “手动更新游戏列表” 即可。

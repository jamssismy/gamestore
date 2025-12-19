# gamestore
这是一个复古游戏安装程序，可以在系统当中构建一个 game store 的选项。并在该选项分类下生成一个 NES 的程序。进入程序可下载一万多款NES复古游戏，并自动安装到模拟器的NES分类下。需手动更新游戏列表，NES分类下游戏就会出现。

安装方法：

一键安装命令： curl -L https://raw.githubusercontent.com/jamssismy/gamestore/main/install.sh | bash

手动安装：

下载完整程序压缩包，解压后将 "es_systems_gamestore.cfg" 文件放入 "/userdata/system/configs/emulationstation/" 文件夹。 
在 "/userdata/roms/" 文件夹内创建 "gamestore" 文件夹，将解压包内 NES 文件夹放入 "/userdata/roms/gamestore/" 文件夹内。
手动更新游戏列表即可。

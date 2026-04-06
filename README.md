# id3gbk

也许只有简中互联网才会遇到这个问题。ID3 规范不支持 GBK，很多歌曲信息是 GBK 编码但标记为 latin1，在 Windows 和 foobar2000 上都乱码了。

感谢 https://github.com/feeluown/feeluown-local 提供的思路和解释，我本打算修改 mutagen 源码来着。

## CHANGELOG

2022/12/29 01:48 创建 .gitignore
2022/12/31 16:04 完成第一版、ID3 支持
2023/06/24 23:41 增加 APE 支持
2026/04/06 17:33 改用 pyproject.toml 管理，删除 id3gbk.ps1 垫片

# 操作历史备忘

## 安装 uv

```cmd
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## pip 国内源

https://pip.pypa.io/en/stable/topics/configuration/

将如下内容写入 `$env:APPDATA\pip\pip.conf` 文件。

```conf
[global]
index-url=https://pypi.tuna.tsinghua.edu.cn/simple

[install]
trusted-host=pypi.tuna.tsinghua.edu.cn
```

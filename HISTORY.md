# 操作历史备忘

## 初始化环境

```ps1
pyenv install
python -m venv venv
. venv/bin/activate
python -m pip install -U pip wheel setuptools
pip install -U -r requirements-dev.txt
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

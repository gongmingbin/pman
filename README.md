# pman 管理密码的命令行工具
pamn是一个用python3写的密码管理工具，密码通过RSA加密保存在sqllite中，只要私钥和key_password不丢，可确保数据安全。

# 使用
- 初始化

```bash
pman.py init
```
- 添加

```bash
pman.py add -d example.com -a xxx@example.com
```


- 列出数据

```bash
pman.py list
```

- 查询

```bash
pman.py query -d example.com -a xxx@example.com
```
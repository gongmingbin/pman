#!/usr/bin/env python3

from pathlib import Path

APP_NAME = 'pman'
DB_NAME = 'password_data'
DB_FILE_NAME = 'password_data.db'


def data_path():
    return Path.home().joinpath('.' + APP_NAME)


def init():
    import getpass
    password = getpass.getpass("enter manage key_password:")
    p = data_path()
    if not p.exists():
        p.mkdir()
    to_data_dir()
    if p.joinpath("key.pem").exists():
        raise Exception("key exist!!! remove it if you want to abandon data")
    import subprocess
    subprocess.call(f" openssl genrsa -aes128 -passout pass:{password} -out key.pem", shell=True)
    subprocess.call(f"openssl rsa -passin pass:{password} -in key.pem -out key.pub -pubout", shell=True)
    execute_sql(f"""
    CREATE TABLE {DB_NAME}(
   id INTEGER PRIMARY KEY   AUTOINCREMENT,
   domain           VARCHAR(100)    NOT NULL,
   account          VARCHAR(100)        NOT NULL,
   password        TEXT NOT NULL ,
   remark  TEXT
    );
    """)
    execute_sql(f"""
    CREATE UNIQUE INDEX domain_account_unique
on {DB_NAME} (domain,account);
    """)


def to_data_dir():
    p = data_path()
    import os
    os.chdir(p)


def add(domain: str, account: str):
    to_data_dir()
    import getpass
    password = getpass.getpass("enter password for {}:".format(account))

    import subprocess
    status, output = subprocess.getstatusoutput(
        f'bash -c \'openssl rsautl -in <(echo "{password}")   -pubin -inkey key.pub -encrypt  | base64\'')
    if status != 0:
        raise Exception("open ssl encrypt err output:" + output)
    execute_sql(f"""
    insert into {DB_NAME}(domain,account,password)VALUES(?,?,?)
    """,
                (domain, account, output)
                )


def query_password(domain: str, account: str, key_password: str):
    to_data_dir()
    res = fetchone(f"select password from {DB_NAME} where domain=? and account=?", (domain, account))
    if not res:
        raise Exception(f"data not exist domain:{domain} account:{account}")
    password = res[0]
    print(decode_password(password, key_password))


def delete_data(domain: str, account: str):
    rowcnt = execute_sql(f"delete from {DB_NAME} where domain=? and account=?", (domain, account)).rowcount
    print("{} row data del".format(rowcnt))


def decode_password(password, key_password):
    import subprocess
    return subprocess.getoutput(f'bash -c '
                                f'\'openssl rsautl '
                                f'-in <(base64 -D <(echo "{password}"))  '
                                f'-inkey key.pem '
                                f'-decrypt '
                                f'-passin '
                                f'pass:"{key_password}"\'')


def query_account(domain: str):
    to_data_dir()
    rows = fetchall(f"select account from {DB_NAME} where domain=?", (domain,))
    for row in rows:
        print(row[0])


def list_data(domain = None,account = None):
    to_data_dir()
    sql = f"select domain,account from {DB_NAME} where 1=1"
    if domain:
        sql += f" and domain='{domain}'"
    if account:
        sql += f" and account='{account}'"
    rows = fetchall(sql)

    print("domain    account")
    for row in rows:
        print(f"{row[0]}    {row[1]}")



def execute_sql(sql, params=None):
    to_data_dir()
    h = SqliteHandle(DB_FILE_NAME)
    return h.execute(sql, params)


def fetchone(sql, params=None):
    return execute_sql(sql, params).fetchone()


def fetchall(sql, params=None):
    return execute_sql(sql, params).fetchall()


class SqliteHandle:
    def __init__(self, dbnam: str):
        self.dbname = dbnam

    def execute(self, sql, params=None):
        import sqlite3
        with sqlite3.connect(self.dbname) as conn:
            if params:
                return conn.execute(sql, params)
            else:
                return conn.execute(sql)



import argparse

parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(dest='command')

add_cmd = subparsers.add_parser('add')
add_cmd.add_argument('-d', '--domain')
add_cmd.add_argument('-a', '--account')

list_cmd = subparsers.add_parser('list')
list_cmd.add_argument('-d', '--domain')
list_cmd.add_argument('-a', '--account')

rm_cmd = subparsers.add_parser('rm')
rm_cmd.add_argument('-d', '--domain')
rm_cmd.add_argument('-a', '--account')

query_cmd = subparsers.add_parser('query')
query_cmd.add_argument('-d', '--domain')
query_cmd.add_argument('-a', '--account')

init_cmd = subparsers.add_parser('init')



args = parser.parse_args()

to_data_dir()

if args.command == 'list':
    list_data(domain=args.domain,account=args.account)
elif args.command == 'add':
    add(args.domain, args.account)
elif args.command == 'rm':
    delete_data(args.domain, args.account)
elif args.command == 'query':
    import getpass
    key_password = getpass.getpass("enter key_password:")
    query_password(args.domain, args.account, key_password)
elif args.command == 'init':
    init()
else:
    raise Exception("something wrong happen! command:"+args.command)

import requests
from datetime import datetime

AZURE_SQL_CONNECTIONSTRING='Driver={ODBC Driver 18 for SQL Server};Server=tcp:server-twitter.database.windows.net,1433;Database=twitter-account;Uid=cdespaux;Pwd=database1!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'


import os
import pyodbc, struct
from azure import identity

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

class account(BaseModel):
    username: str
    predict: int
    call: int
    date: str
    
connection_string = AZURE_SQL_CONNECTIONSTRING

app = FastAPI()

@app.get("/")
def root():
    print("Root of Person API")
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # Table should be created ahead of time in production app.
        cursor.execute("""
            CREATE TABLE account (
                username varchar(255) NOT NULL PRIMARY KEY IDENTITY,
                predict int,
                call int,
                date string
            );
        """)

        conn.commit()
    except Exception as e:
        # Table may already exist
        print(e)
    return "Person API"

@app.get("/all")
def get_persons():
    rows = []
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account")

        for row in cursor.fetchall():
            rows.append(f"{row.username}, {row.predict}, {row.call}, {row.date}")
    return rows

@app.get("/account/{username}")
def get_person(username: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account WHERE username = ?", username)

        row = cursor.fetchone()
        return f"{row.username}, {row.predict}, {row.call}, {row.date}"

@app.post("/account/")
def create_person(account: account):
    print(account)
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO account (username, predict, call, date) VALUES (?, ?, ?, ?)", account.username, account.predict, account.call, account.date)
        conn.commit()
    return account


@app.patch("/accountCall/{username}")
def update_person(username: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE account SET call = call+1 WHERE username = ?",  username)
        conn.commit()

@app.patch("/accountDate/{username}")
def update_person(username: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE account SET date = ? WHERE username = ?", datetime.now().strftime("%Y-%m-%d"), username)
        conn.commit()


def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn
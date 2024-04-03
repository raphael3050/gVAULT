import uuid
import sqlite3
import secrets
import random
import os
from string import hexdigits
from binascii import hexlify

import grpc
from Crypto.Cipher import AES
from concurrent import futures
import vault_pb2
import vault_pb2_grpc


DATABASE = "users.db"
KEY = os.urandom(32)
print("AES Key : ",KEY)


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            master_password TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL,
            password TEXT NOT NULL,
            fk_username TEXT NOT NULL,
            FOREIGN KEY (fk_username) REFERENCES users(username)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            token TEXT PRIMARY KEY,
            fk_username TEXT NOT NULL,
            FOREIGN KEY (fk_username) REFERENCES users(username)
        )
        """)
        conn.execute(f"""
        INSERT INTO users (username, master_password) VALUES ("admin", "{os.getenv('FLAG_1', 'F4J{FAKE_FLAG_1}')}")
        """)
        conn.execute(f"""
        INSERT INTO passwords (label, password, fk_username) VALUES (
            "flag",
            "{aes_encrypt(os.getenv('FLAG_2', 'F4J{FAKE_FLAG_2}'))}",
            "admin"
        )
        """)

def aes_encrypt(plaintext):
    nonce = (random.choice(hexdigits) * 8).encode()
    cipher = AES.new(KEY, AES.MODE_CTR, nonce=nonce)
    ciphertext = cipher.encrypt(plaintext.encode())
    return hexlify(ciphertext).decode("utf-8")

def aes_decrypt(nonce, ciphertext):
    cipher = AES.new(KEY, AES.MODE_CTR, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext).decode()
    return plaintext

class PasswordVaultServicer(vault_pb2_grpc.PasswordVaultServicer):
    def StorePassword(self, request, context):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fk_username FROM user_tokens WHERE token=?", (request.token,))
            row = cursor.fetchone()
            if not row:
                return vault_pb2.StoreResponse(status="Invalid token")

            username = row[0]
            encrypted_password = aes_encrypt(request.password)
            try:
                conn.execute("INSERT INTO passwords (label, password, fk_username) VALUES (?, ?, ?)", 
                            (request.label, encrypted_password, username))
                return vault_pb2.StoreResponse(status="Password stored successfully")
            except sqlite3.Error as e:
                return vault_pb2.StoreResponse(status=f"Error: {e}")

    def RetrievePassword(self, request, context):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fk_username FROM user_tokens WHERE token=?", (request.token,))
            row = cursor.fetchone()
            if not row:
                return vault_pb2.RetrieveResponse(passwords={})
            
            username = row[0]
            cursor.execute("SELECT label, password FROM passwords WHERE fk_username=?", (username,))
            rows = cursor.fetchall()
            if rows:
                passwords = {row[0]: row[1] for row in rows}
                return vault_pb2.RetrieveResponse(passwords=passwords)
            else:
                return vault_pb2.RetrieveResponse(passwords={})

    def Register(self, request, context):
        with sqlite3.connect(DATABASE) as conn:
            try:
                conn.execute("INSERT INTO users (username, master_password) VALUES (?, ?)", (request.username, request.master_password))
                return vault_pb2.UserResponse(status="success", message="User registered successfully")
            except sqlite3.IntegrityError:
                return vault_pb2.UserResponse(status="error", message="Username already exists")

    def Login(self, request, context):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT master_password FROM users WHERE username=?", (request.username,))
            row = cursor.fetchone()
            if row and row[0] == request.master_password:
                conn.execute("DELETE FROM user_tokens WHERE fk_username=?", (request.username,))
                token = str(uuid.uuid4())
                conn.execute("INSERT INTO user_tokens (token, fk_username) VALUES (?, ?)", (token, request.username))
                return vault_pb2.UserResponse(status="success", message=token)
            else:
                return vault_pb2.UserResponse(status="error", message="Invalid credentials")

    def SearchUsersByName(self, request, context):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT username FROM users WHERE username LIKE '%{request.name}%'")
            results = cursor.fetchall()
            usernames = [row[0] for row in results]
            return vault_pb2.SearchResponse(usernames=usernames)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vault_pb2_grpc.add_PasswordVaultServicer_to_server(PasswordVaultServicer(), server)
    server.add_insecure_port('0.0.0.0:50051')
    print("Starting server...")
    server.start()
    print("Server started. Listening on port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    init_db()
    serve()

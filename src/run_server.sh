#!/bin/bash

# 1) Cleaning
rm -rf users.db venv/ __pycache__/ vault_pb2_grpc.py vault_pb2.py

# 2) Building
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. vault.proto

# 3) Running
python3 vault_server.py

import sys

import grpc
import vault_pb2
import vault_pb2_grpc
import uuid


TOKEN = None

def store_password(channel, label, password):
    stub = vault_pb2_grpc.PasswordVaultStub(channel)
    response = stub.StorePassword(vault_pb2.StoreRequest(token=TOKEN, label=label, password=password))
    print(response.status)

def retrieve_password(channel):
    stub = vault_pb2_grpc.PasswordVaultStub(channel)
    response = stub.RetrievePassword(vault_pb2.RetrieveRequest(token=TOKEN))
    if response.passwords:
        print("Passwords:")
        for label, password in response.passwords.items():
            print("\t-", label, ":", password)
    else:
        print("No passwords found for this user.")

def register_user(channel, username, master_password):
    stub = vault_pb2_grpc.PasswordVaultStub(channel)
    response = stub.Register(vault_pb2.UserRequest(username=username, master_password=master_password))
    print(response.message)

def login_user(channel, username, master_password):
    global TOKEN
    stub = vault_pb2_grpc.PasswordVaultStub(channel)
    response = stub.Login(vault_pb2.UserRequest(username=username, master_password=master_password))
    if response.status == "success":
        TOKEN = response.message
        print("Login successful!")
    else:
        print(response.message)

def search_users_by_name(channel, name):
    stub = vault_pb2_grpc.PasswordVaultStub(channel)
    response = stub.SearchUsersByName(vault_pb2.SearchRequest(name=name))
    usernames = response.usernames
    if not usernames:
        print("No users found.")
        return
    
    if len(usernames) == 1: print(f"{len(usernames)} user found:")
    else: print(f"{len(usernames)} users found:")

    for username in usernames:
        print("\t-", username)

def show_help():
    print("=" * 12, "Options", "=" * 12)
    print("1. Register user")
    print("2. Login user")
    print("3. Store password")
    print("4. Retrieve my passwords (not fully implemented - missing decryption)")
    print("5. Search users by name")
    print("6. Exit")

def repl():
    with grpc.insecure_channel('localhost:50051') as channel:
        show_help()
        while True:
            choice = input("\nEnter your choice: ")
            if choice == "1":
                username = input("Enter username: ")
                master_password = input("Enter master password: ")
                register_user(channel, username, master_password)
            elif choice == "2":
                username = input("Enter username: ")
                master_password = input("Enter master password: ")
                login_user(channel, username, master_password)
            elif choice == "3":
                if not TOKEN:
                    print("You need to be logged in to store passwords.")
                    continue
                label = input("Enter password label: ")
                password = input("Enter password: ")
                store_password(channel, label, password)
            elif choice == "4":
                if not TOKEN:
                    print("You need to be logged in to retrieve passwords.")
                    continue
                retrieve_password(channel)
            elif choice == "5":
                username = input("Enter username: ")
                search_users_by_name(channel, username)
            elif choice == "6":
                print("Exiting...")
                break
            elif choice in ["help", "?"]:
                show_help()
            else:
                print("Invalid choice. Please try again.")
                print("Type 'help' or '?' to see the options.")

if __name__ == '__main__':
    try:
        repl()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

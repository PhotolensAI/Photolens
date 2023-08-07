import firebase_admin
from firebase_admin import credentials, db, storage, auth
import base64
from datetime import datetime
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# cred init
db_key = os.environ["PRIVATE_KEY"]
db_key_id = os.environ["PRIVATE_KEY_ID"]
cred_file = json.loads(open("services/firebase_sdk_secret.json", "r").read())
cred_file["private_key"] = db_key
cred_file["private_key_id"] = db_key_id
API_KEY = os.environ["API_KEY"]
open("services/firebase_sdk_secret_mod.json", "w").write(json.dumps(cred_file))

cred = credentials.Certificate("services/firebase_sdk_secret_mod.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://photolensdb-default-rtdb.firebaseio.com/", "storageBucket": "photolensdb.appspot.com"})


### core funcs
def is_img_path_taken(username, conversation_name, path):
    for msg in read_conversation(username, conversation_name):
        try:
            if msg["image_path"] == path:
                return True
        except:
            pass
    return False


def add_img_path(username, conversation_name, path):
    ref = db.reference(f"messages/{username}/{conversation_name}")
    messages = ref.get()
    if messages is None:
        messages = []
    
    messages[len(messages)-1]["image_path"] = path
    ref.set(messages)


def get_img_bytes_from_link(link):
    response = requests.get(link)
    return response.content




### realtime db
def add_msg(role, username, conversation_name, message=None, func_call_obj=None):
    now = datetime.now()
    ref = db.reference(f"messages/{username}/{conversation_name}")
    messages = ref.get()
    if messages is None:
        messages = []

    if func_call_obj:
        messages.append({"role": role, "content": None, "function": func_call_obj, "time": int(now.strftime("%H%M%S"))})
    else:
        messages.append({"role": role, "content": message, "image_path": "", "time": int(now.strftime("%H%M%S"))})
    ref.set(messages)


def get_last_img_path(username, conversation_name):
    i = len(read_conversation(username, conversation_name))
    while i:
        i -= 1
        if read_conversation(username, conversation_name)[i]["image_path"]:
            return read_conversation(username, conversation_name)[i]["image_path"]


def delete_msg(user_name, conversation_name, message_index):
    ref = db.reference(f"messages/{user_name}/{conversation_name}")
    messages = ref.get()
    if messages is not None and 0 <= message_index < len(messages):
        del messages[message_index]
        ref.set(messages)


def read_conversation(user_name, conversation_name):
    ref = db.reference(f"messages/{user_name}/{conversation_name}")
    messages = ref.get()
    if messages == None:
        messages = []
    return messages




### storage
def download_img(username, conversation_name, img_local_path, img_db_path):
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=f"{username}/{conversation_name}/{img_db_path}")
    for blob in blobs:
        if blob.name == f"{username}/{conversation_name}/{img_db_path}":
            blob.download_to_filename(img_local_path)


def get_img(username, conversation_name, img_name_with_png):
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=f"{username}/{conversation_name}/{img_name_with_png}")

    for blob in blobs:
        if blob.name == f"{username}/{conversation_name}/{img_name_with_png}":
            return base64.b64encode(blob.download_as_string()).decode("utf-8")

    return None


def upload_img(username, conversation_name, img_bytes_in_string):
    bucket = storage.bucket()
    img_name = -1

    while True:
        img_name += 1
        path = f"{str(img_name)}"

        if not is_img_path_taken(username, conversation_name, path):
            add_img_path(username, conversation_name, path)
            blob = bucket.blob(username + "/" + conversation_name + "/" + path)
            blob.content_type = "image/png"
            blob.upload_from_string(img_bytes_in_string, content_type=blob.content_type)
            break

        else:
            pass



### auth
def create_new_user(username, email, password):
    try:
        auth.create_user(email=email, password=password, display_name=username)
        return True
    except:
        return False


def check_mail_exists(email):
    try:
        auth.get_user(email)
        return True
    except:
        return False


def authenticate_user(email, password, api_key=API_KEY):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + api_key
    response = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if response.status_code == 200:
        return response.json()
    else:
        return False

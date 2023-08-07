import flask
import asyncio
from routes.query import *
from services.database import *
from dotenv import load_dotenv

load_dotenv()

app = flask.Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/demo", methods=["GET"])
def demo():
    return flask.redirect("/chat")


@app.route("/login", methods=["GET", "POST"])
def login():
    flask.session.clear()
    if flask.request.method == "POST":
        #username = flask.request.form["username"]
        email = flask.request.form["email"]
        password = flask.request.form["password"]

        user = authenticate_user(email, password)
        if user:
            flask.session["username"] = user["displayName"]
            # You can also fetch the conversation_name based on user data or any other logic you have
            flask.session["conversation_name"] = "conversation1"
            return flask.redirect("/chat")

    return flask.render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if flask.request.method == "POST":
        # Extract the username and password from the signup form
        email = flask.request.form["email"]
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        #check if the mail is taken
        if check_mail_exists(email):
            return "Email already taken. Please try again."

        user_id = create_new_user(username, email, password)
        if user_id:
            # You can also fetch the conversation_name based on user data or any other logic you have
            flask.session["conversation_name"] = "conversation1"
            return flask.redirect("/login")
        else:
            return "Error creating user. Please try again."

    return flask.render_template("signup.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if flask.request.method == "POST":
        msg_in = flask.request.form["msg_inp"]
        msg = asyncio.run(query_model(msg_in, flask.session["username"], flask.session["conversation_name"])) #query model

        return flask.render_template("chat.html", msg=msg)

    if flask.request.method == "GET":
        try:
            if not flask.session["username"]:
                return flask.redirect("/login")
        except:
            return flask.redirect("/login")

        try:
            img_bytes = "data:image/jpeg;base64," + get_img(flask.session["username"], flask.session["conversation_name"], get_last_img_path(flask.session["username"], flask.session["conversation_name"]))
        except:
            img_bytes = ""

        msg = {
            "history": read_conversation(flask.session["username"], flask.session["conversation_name"]),
            "img_bytes": img_bytes
        }

    return flask.render_template("chat.html", msg=msg)

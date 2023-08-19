from flask import Flask, request, jsonify
import asyncio
import services.tools as tools
import services.database as db

app = Flask(__name__)
api_responses = {}



async def query_model(msg_inp: str, username: str, conversation_name: str):
    msg_out = await tools.send_msg(msg_inp, username, conversation_name)
    current_image_path = db.get_last_img_path(username, conversation_name)

    response = {
        "msg_out": msg_out,
        "history": db.read_conversation(username, conversation_name),
    }
    if current_image_path is not None:
        img = db.get_img(username, conversation_name, current_image_path)
        response["img_bytes"] = img

    return response



@app.route("/")
def index():
    """
    A function that serves as the route handler for the root URL ("/"). 
    This function returns a JSON response with the body {"working": True}.

    Args:
    - None

    Returns:
    - A JSON response with the body {"working": True}
    """
    return jsonify({"working": True})



@app.route("/query", methods=["POST"])
def query():
    """
    Handles a GET request to the "/query" endpoint of the API.
    
    Args:
        - msg_inp (str): The input message to be queried.
        - username (str): The username of the person making the query.
        - conversation_name (str): The name of the conversation to query.
    """
    api_responses[request.args.get("username")] = {"STATUS": "Processing"}
    output = asyncio.run(query_model(request.args.get("msg_inp"), request.args.get("username"), request.args.get("conversation_name")))
    output["STATUS"] = "Done"
    api_responses[request.args.get("username")] = output
    #return status
    return jsonify(True)

@app.route("/get_query", methods=["GET"])
def get_query():
    """
    Retrieves a query from the API based on the provided username.

    Args:
        Username (str): The username of the person making the query.

    Returns:
        - A JSON response containing the output of the query.
        - STATUS (str): The status of the query: "Processing" or "Done".
    """
    return api_responses[request.args.get("username")]

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
import asyncio
from routes.query import query_model

app = Flask(__name__)



@app.route("/")
def index():
    """
    A function that serves as the route handler for the root URL ("/"). 
    This function returns a JSON response with the body {"working": True}.

    Parameters:
    - None

    Returns:
    - A JSON response with the body {"working": True}
    """
    return jsonify({"working": True})



@app.route("/query", methods=["GET"])
def query():
    """
    Handles a GET request to the "/query" endpoint of the API.
    
    Parameters:
        - msg_inp (str): The input message to be queried.
        - username (str): The username of the person making the query.
        - conversation_name (str): The name of the conversation to query.
    
    Returns:
         - A JSON response containing the output of the query.
    """
    output = asyncio.run(query_model(request.args.get("msg_inp"), request.args.get("username"), request.args.get("conversation_name")))
    print(output)
    return output

if __name__ == "__main__":
    app.run(debug=True)

import services.tools as tools
import services.database as db


async def query_model(msg_inp: str, username: str, conversation_name: str):
    msg_out = await tools.send_msg(msg_inp, username, conversation_name)
    current_image_path = db.get_last_img_path(username, conversation_name)

    response = {
        "msg_out": msg_out,
        "history": db.read_conversation(username, conversation_name),
    }
    if current_image_path is not None:
        img = db.get_img(username, conversation_name, current_image_path)
        response["img_bytes"] = f"data:image/jpeg;base64,{img}"

    return response

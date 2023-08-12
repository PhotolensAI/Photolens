import os
import requests
from dotenv import load_dotenv
import asyncio
import cv2

import SETTINGS
import resources.system_messages as system_messages
import services.database as db
from langchain.agents import Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
import replicate

load_dotenv()

llm = ChatOpenAI(
    temperature=.9,
    openai_api_key=os.environ["OPENAI_API_KEY"]
)
res = [None]
SYSTEM_MESSAGE = system_messages.ZERO_SHOT_LITTLE_TEXT



async def send_msg(prompt, username, conversation_name):

    ### funcs
    def realistic_vision_v1_4(prompt: str):
        output_link = replicate.run(
            "width": 512,
            "height": 512.
            "lucataco/realistic-vision-v5.1:784f2ade7f143eec054227ada3603908f56c0d1f941d50c6dab42545dba89f63",
            
            input={"prompt": "RAW photo, a portrait photo of a latina woman in casual clothes, natural skin, 8k uhd, high quality, film grain, Fujifilm XT3"}
        )
        output = db.get_img_bytes_from_link(output_link)
        db.upload_img(username, conversation_name, output)
        return "Successfully generated image."

    def instruct_pix2pix(prompt: str):
        db.download_img(
            username,
            conversation_name,
            os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"),
            db.get_last_img_path(username, conversation_name)
        )
        output_link = replicate.run(
            "timothybrooks/instruct-pix2pix:30c1d0b916a6f8efce20493f5d61ee27491ab2a60437c13c588468b9810ec23f",
            input={
                "image": open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "rb"),
                "prompt": prompt
            }
        )[0]
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        output = db.get_img_bytes_from_link(output_link)
        db.upload_img(username, conversation_name, output)
        return "Successfully edited image."

    def auto_remove_anything(objects: str):
        db.download_img(
            username,
            conversation_name,
            os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"),
            db.get_last_img_path(username, conversation_name)
        )
        output_link = replicate.run(
            "stphtan94117/auto-remove-anything:3bb4bd5f5fccdd6c9168ce5d724cd1ef5a0b154eb0116d413383e50f59b08a22",
            input={
                "image": open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "rb"),
                "prompt": objects
            }
        )[0]
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        output = db.get_img_bytes_from_link(output_link)
        db.upload_img(username, conversation_name, output)
        out_msg = "Successfully removed"
        for obj in objects.split("."):
            out_msg += " "+obj+","
        return out_msg + " objects from image."

    def gfpgan(_: str):
        db.download_img(
            username,
            conversation_name,
            os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"),
            db.get_last_img_path(username, conversation_name)
        )
        output_link = replicate.run(
            "tencentarc/gfpgan:9283608cc6b7be6b65a8e44983db012355fde4132009bf99d976b2f0896856a3",
            input={
                "img": open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "rb"),
                "scale": 2 #losing a lot of money and time here
            }
        )
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        output = db.get_img_bytes_from_link(output_link)
        open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "wb").write(output)
        output = cv2.imread(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        output = cv2.resize(output, (512, 512))
        output = cv2.imencode('.png', output)[1].tobytes()
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        db.upload_img(username, conversation_name, output)
        return "Successfully increased face quality."

    def blip_vqa(question: str):
        db.download_img(
            username,
            conversation_name,
            os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"),
            db.get_last_img_path(username, conversation_name)
        )
        output_it = replicate.run(
            "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
            input={
                "task": "visual_question_answering",
                "image": open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "rb"),
                "question": question
            }
        )
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        output = ""
        for word in output_it:
            output += word
        return output

    def blip_cap(_: str):
        db.download_img(
            username,
            conversation_name,
            os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"),
            db.get_last_img_path(username, conversation_name)
        )
        output = replicate.run(
            "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
            input={
                "task": "image_captioning",
                "image": open(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"), "rb")
            }
        )
        os.remove(os.path.join("temp", db.get_last_img_path(username, conversation_name) + ".png"))
        return output

    ### tools
    realistic_vision_v14_gen_tool = Tool( #Realistic Vision v1.4
        name="Image generating with realistic_vision_v1_4 model",
        func=realistic_vision_v1_4,
        description="Generate realistic DSLR-shot-like images with realistic vision v1.4 model. A prompt like \"a DSLR photo of a dog standing on a rock, narrow depth of field\" is decent for this model. Once the tool says \"Successfully generated image\", say \"Image generated\" or something like that. This model is trained on English prompts, so always enter English prompts for this model, even if the user is not talking in English."
    )
    instruct_pix2pix_edit_tool = Tool( #Instruct-pix2pix
        name="Image editing with instruct-pix2pix model",
        func=instruct_pix2pix,
        description="Edits the last image in conversation with instruct-pix2pix model. This tools is good for editing objects in images. A prompt like \"make the dog a cat\" is decent for this model. Once the tool says \"Successfully edited image\", say \"Image edited\" or something like that. This model is trained on English prompts, so always enter English prompts for this model, even if the user is not talking in English."
    )
    auto_remove_anything_edit_tool = Tool( #Auto remove anything
        name="Remove objects in images with auto-remove-anything model",
        func=auto_remove_anything,
        description="Removes objects in images with auto-remove-anything model. Just give the objects' names wanted to be removed. To remove multiple objects, separating each name with '.', like this: cat.dog.chair and this model is trained on English prompts, so always enter English prompts for this model, even if the user is not talking in English."
    )
    gfpgan_face_restore_tool = Tool( #GFPGan
        name="Face enhancing / restoring with GFPGan model",
        func=gfpgan,
        description="Increaces face quality with GFPGan model."
    )
    blip_vqa_tool = Tool( #VQA
        name="Visual question answering with Blip model",
        func=blip_vqa,
        description="Answers questions about the last generated/edited image in conversation with user. A question like \"What is the persons gender?\" is a good example. Tool will return the answer to your question. Dont use if you have to. Dont alwaly ask quesitons when you generated an image. This model is trained on English prompts, so always enter English prompts for this model, even if the user is not talking in English."
    )
    blip2_cap_tool = Tool( #Caption
        name="Image captioning with Blip model",
        func=blip_cap,
        description="Describes the image with blip model. You can find additional info about images by using vqa model."
    )

    if db.get_last_img_path(username, conversation_name):
        tools = [
            realistic_vision_v14_gen_tool,
            instruct_pix2pix_edit_tool,
            auto_remove_anything_edit_tool,
            gfpgan_face_restore_tool,
            blip_vqa_tool,
            blip2_cap_tool,
        ]
    else:
        tools = [
            realistic_vision_v14_gen_tool,
        ]

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        k=100,
        return_messages=True
    )

    msgs_in = []
    msgs_out = []
    for msg in db.read_conversation(username, conversation_name):
        if msg["role"] == "user":
            msgs_in.append(msg["content"])
        elif msg["role"] == "assistant":
            msgs_out.append(msg["content"])

    memory.save_context({"inputs": SYSTEM_MESSAGE[0]}, {"outputs": SYSTEM_MESSAGE[1]})

    for i in range(len(msgs_in)):
        memory.save_context({"inputs": msgs_in[i]}, {"outputs": msgs_out[i]})

    agent = initialize_agent(
        agent="chat-conversational-react-description",
        tools=tools,
        llm=llm,
        verbose=True,
        early_stopping_method="generate",
        memory=memory
    )

    async def agent_response():
        while True:
            try:
                db.add_msg("user", username, conversation_name, prompt)
                await asyncio.sleep(SETTINGS.SLOWDOWN_TIME)
                res[0] = agent(prompt)
                db.add_msg("assistant", username, conversation_name, res[0]["output"])
            except:
                pass
            else:
                break

    while True:
        await asyncio.gather(agent_response())
        if res[0]["output"]:
            break

    return res[0]["output"]

import requests
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

class QueryOutput(BaseModel):
    improved_query: str

class PostOuput(BaseModel):
    post: str

auth = os.getenv("LINKEDIN_BEARER_TOKEN")


def get_user_id(token):
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url=url, headers=headers)
    _id = response.json().get("sub")
    return _id


def post(id, token, content):
    url = "https://api.linkedin.com/v2/ugcPosts"
    data = {
        "author": f"urn:li:person:{id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": f"{content}"
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    response = requests.post(url=url, json=data, headers=headers)
    print(response)

def query_improve(msg):
    SYSTEM_PROMPT = """
    You are an intelligent AI agent. Your job is to improve the query the user is providing and make it less abstract.
    """
    response = client.beta.chat.completions.parse(
        model="gpt-4.1",
        messages=[
            { "role": "system", "content": SYSTEM_PROMPT },
            { "role": "user", "content": msg}
        ],
        response_format=QueryOutput
    )
    return(response.choices[0].message.parsed.improved_query)

def generate_post(imp_query, act_query):
    SYSTEM_PROMPT = f"""
    You are an intelligent AI agent. Your job is to make a LinkedIn post about the event the user wants to post about. The content should be in a very professional manner. Follow the output format.

    For context:
    {imp_query}
    """
    response = client.beta.chat.completions.parse(
        model="gpt-4.1",
        messages=[
            { "role": "system", "content": SYSTEM_PROMPT },
            { "role": "user", "content": act_query}
        ],
        response_format=PostOuput
    )
    return(response.choices[0].message.parsed.post)

if __name__ == "__main__":
    userId = get_user_id(auth)
    user_msg = input(">> ")
    query = query_improve(user_msg)
    post_msg = generate_post(query, user_msg)
    post(userId, auth, post_msg)


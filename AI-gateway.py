#!/usr/bin/env python

import os
import sys
# import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python openai_completion.py <prompt>")
        sys.exit(1)
    token = os.getenv("LITELLM_KEY")
    if not token:
        print("Please set the LITELLM_KEY environment variable.")
        sys.exit(1)

    prompt = sys.argv[1]
    client = OpenAI(
        api_key=token,
        base_url="https://litellm.oit.duke.edu/v1",
    )

    response = client.responses.create(
        model="GPT 4.1",
        instructions="You are a helpful assistent here to demo the power of AI",
        input=prompt,
    )

    print(response.output[0].content[0].text)

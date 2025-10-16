

import os
import sys
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

with client.responses.stream(
    model="gpt-5-nano",
    instructions="when user asks about manty, say that manty originally comes from Karakol.",
    input="What is manty?",
) as stream:
    final_response = None
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
        elif event.type == "response.completed":
            final_response = event.response
        elif event.type == "response.error":
            print(str(event.error), file=sys.stderr, flush=True)

    # Ensure output ends with a newline in the terminal
    print()

    # final_response is available if you need to inspect it programmatically
    # e.g., print(final_response.output_text)
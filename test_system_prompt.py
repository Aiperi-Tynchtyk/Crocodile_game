#!/usr/bin/env python3
"""Test script to verify system prompt behavior"""

import os
import sys
from openai import OpenAI

def test_system_prompt():
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    system_prompt = {
        "role": "system", 
        "content": "You are a cheerful game host who gives hints only when the player asks nicely."
    }
    
    # Test 1: Ask for a clue
    print("=== Test 1: Asking for a clue ===")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            system_prompt,
            {"role": "user", "content": "Give me a clue for a cat"}
        ]
    )
    print(f"AI Response: {response.choices[0].message.content}")
    
    # Test 2: Ask nicely for a hint
    print("\n=== Test 2: Asking nicely for a hint ===")
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            system_prompt,
            {"role": "user", "content": "Please, could you give me a hint about this animal?"}
        ]
    )
    print(f"AI Response: {response.choices[0].message.content}")
    
    # Test 3: Ask rudely for a hint
    print("\n=== Test 3: Asking rudely for a hint ===")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            system_prompt,
            {"role": "user", "content": "Just tell me the answer already!"}
        ]
    )
    print(f"AI Response: {response.choices[0].message.content}")

if __name__ == "__main__":
    test_system_prompt()

import os
import json
import sys
import random
from typing import Tuple
from openai import OpenAI


def create_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set in the environment.", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key)


def select_difficulty() -> str:
    print("Choose difficulty:")
    print("  1) Easy   - more obvious, accessible clues")
    print("  2) Medium - balanced clues")
    print("  3) Hard   - subtle, more cryptic clues")
    while True:
        choice = input("Enter 1/2/3: ").strip()
        mapping = {"1": "easy", "2": "medium", "3": "hard"}
        if choice in mapping:
            return mapping[choice]
        print("Please enter 1, 2, or 3.")


def select_category_and_animal() -> Tuple[str, str]:
    categories = {
        "mammals": [
            "cat", "dog", "elephant", "giraffe", "lion", "tiger", "zebra", "panda", "kangaroo", "dolphin", "whale", "bear",
        ],
        "birds": [
            "eagle", "penguin", "sparrow", "owl", "parrot", "flamingo", "peacock", "duck", "swan", "falcon",
        ],
        "reptiles": [
            "crocodile", "alligator", "snake", "lizard", "turtle", "tortoise", "iguana", "chameleon",
        ],
    }

    print("Choose a category:")
    print("  1) Mammals  2) Birds  3) Reptiles")
    mapping = {"1": "mammals", "2": "birds", "3": "reptiles"}
    category = None
    while category is None:
        choice = input("Enter 1/2/3: ").strip()
        category = mapping.get(choice)
        if not category:
            print("Please enter 1, 2, or 3.")
    animal = random.choice(categories[category])
    return category, animal


def get_clue_for_animal(client: OpenAI, animal: str, difficulty: str) -> str:
    """Generate a single clue for the given animal tailored by difficulty.
    Easy: more obvious; Medium: balanced; Hard: subtle/cryptic.
    Returns the clue string.
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are a cheerful word guessing game host. "
            "You give short, friendly hints and never reveal the answer directly. "
            "Encourage the user after every guess."
        )
    }
    
    difficulty_guidance = {
        "easy": "Provide a clear, fairly obvious clue a casual player could guess.",
        "medium": "Provide a balanced clue that suggests but doesn't give away.",
        "hard": "Provide a subtle, cryptic clue focusing on less-known traits.",
    }
    system_instructions = (
        "You are a cheerful Game Master for a guessing game. "
        "Produce ONE concise clue for the specified animal. Do NOT reveal the animal's name. "
        "Respond ONLY as a strict JSON object with key 'clue'."
    )
    user_prompt = (
        f"Animal: '{animal}'. Difficulty: '{difficulty}'.\n"
        f"Guidance: {difficulty_guidance.get(difficulty, '')}\n"
        "Return JSON like {\"clue\": \"I purr and love naps on sunny windowsills.\"}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            system_prompt,
            {"role": "user", "content": user_prompt}
        ]
    )
    text = resp.choices[0].message.content.strip()
    print(f"[DEBUG] AI Response: {text}")  # Debug output
    try:
        data = json.loads(text)
        clue = str(data.get("clue", "")).strip()
        if clue:
            return clue
    except json.JSONDecodeError:
        pass
    # Fallback constructive clues per difficulty
    if difficulty == "easy":
        return "This animal has a very distinctive feature that most people recognize immediately - think about what makes it unique!"
    if difficulty == "hard":
        return "Focus on a subtle characteristic - perhaps its hunting style, sleeping habits, or a lesser-known physical trait."
    return "Consider both its habitat and a specific behavior pattern - where does it live and what does it do there?"


def validate_guess_with_llm(client: OpenAI, animal: str, guess: str) -> bool:
    """Ask the model if the guess matches the secret animal (allowing synonyms and case-insensitive match).
    Returns True if it's a match, False otherwise.
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are a cheerful word guessing game host. "
            "You give short, friendly hints and never reveal the answer directly. "
            "Encourage the user after every guess."
        )
    }

    user_prompt = (
        f"Secret animal: '{animal}'. User guess: '{guess}'.\n"
        "Respond strictly as JSON, e.g., {\"match\": true}."
    )

    resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        system_prompt,
        {"role": "user", "content": user_prompt}
    ],
    max_tokens=80,     # keeps clues concise
    temperature=0.7,   # gives creative, friendly clues
    top_p=0.9          # balances creativity and consistency
)
    text = resp.choices[0].message.content.strip()
    print(f"[DEBUG] Validation response: {text}")  # Debug output
    try:
        data = json.loads(text)
        match = data.get("match")
        print(f"[DEBUG] Match result: {match}")  # Debug output
        return bool(match)
    except json.JSONDecodeError:
        print(f"[DEBUG] JSON parse failed, using fallback")  # Debug output
        # Fallback heuristic if JSON parsing failed
        normalized_animal = animal.lower().strip()
        normalized_guess = guess.lower().strip()
        result = normalized_animal == normalized_guess
        print(f"[DEBUG] Fallback result: {result}")  # Debug output
        return result


def get_additional_hint(client: OpenAI, animal: str, existing_hints: list[str]) -> str:
    """Ask the model for one more concise hint about the same animal.
    Ensures the hint does not repeat any in existing_hints.
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are a cheerful word guessing game host. "
            "You give short, friendly hints and never reveal the answer directly. "
            "Encourage the user after every guess."
        )
    }

    # Try up to 3 times to get a unique hint from the model
    for _ in range(3):
        user_prompt = (
            f"Secret animal (do not reveal to user): '{animal}'.\n"
            f"Already given hints (do not repeat): {json.dumps(existing_hints)}.\n"
            "Return strictly JSON like {\"hint\": \"I have stripes but am not easily domesticated.\"}"
        )

        resp = client.chat.completions.create(
            model="gpt-5",
            messages=[
                system_prompt,
                {"role": "user", "content": user_prompt}
            ]
        )
        text = resp.choices[0].message.content.strip()
        try:
            data = json.loads(text)
            hint = str(data.get("hint", "")).strip()
            if hint and hint not in existing_hints:
                return hint
        except json.JSONDecodeError:
            continue

    # Fallback constructive unique hints
    fallback_pool = [
        "Think about its natural habitat - where does this animal typically live and what environment suits it best?",
        "Consider its diet and feeding habits - what does it eat and how does it find or catch its food?",
        "Focus on a distinctive physical feature - what unique body part or characteristic makes this animal special?",
        "When is it most active - does it hunt, forage, or move around more during the day or night?",
        "What sounds does it make - does it roar, chirp, hiss, or make other distinctive noises and why?",
    ]
    for candidate in fallback_pool:
        if candidate not in existing_hints:
            return candidate
    # If everything failed, return a generic line guaranteed to differ slightly
    return f"Another angle: think habitat + behavior ({random.randint(1, 9999)})."


def is_polite_request(text: str) -> bool:
    """Check if the user's request is polite/kind."""
    polite_words = ["please", "thank you", "thanks", "kindly", "would you", "could you", "may i"]
    rude_words = ["just", "already", "hurry", "quickly", "now", "damn", "stupid", "idiot", "rude", "mean", "angry", "mad"]
    
    text_lower = text.lower()
    
    # Check for polite indicators
    has_polite = any(word in text_lower for word in polite_words)
    
    # Check for rude indicators
    has_rude = any(word in text_lower for word in rude_words)
    
    # Also check for question marks and exclamation patterns
    has_question = "?" in text
    has_imperative = text.endswith("!") and not has_question
    
    result = has_polite or (has_question and not has_rude) or (not has_imperative and not has_rude)
    print(f"[DEBUG] Text: '{text}' | Polite: {has_polite} | Rude: {has_rude} | Result: {result}")
    return result


def play_single_round(client: OpenAI, category: str, difficulty: str) -> bool:
    animal = random.choice({
        "mammals": [
            "cat", "dog", "elephant", "giraffe", "lion", "tiger", "zebra", "panda", "kangaroo", "dolphin", "whale", "bear",
        ],
        "birds": [
            "eagle", "penguin", "sparrow", "owl", "parrot", "flamingo", "peacock", "duck", "swan", "falcon",
        ],
        "reptiles": [
            "crocodile", "alligator", "snake", "lizard", "turtle", "tortoise", "iguana", "chameleon",
        ],
    }[category])
    clue = get_clue_for_animal(client, animal, difficulty)
    shown_hints: list[str] = [clue]

    print("\nNew round!")
    print(f"Category: {category.capitalize()}, Difficulty: {difficulty.capitalize()}")
    print(f"Clue: {clue}")
    print("🎮 Good luck! I believe in you! 🌟")

    max_attempts = 3
    score = 100
    penalty_per_wrong = 20
    rude_count = 0
    
    for attempt in range(1, max_attempts + 1):
        guess = input(f"Attempt {attempt}/{max_attempts} - Your guess: ")
        if not guess.strip():
            print("Please enter a guess.")
            continue

        is_match = validate_guess_with_llm(client, animal, guess)
        if is_match:
            print("🎉 Congratulations! You guessed it right!")
            print(f"Score: {max(score, 0)}")
            return True
        else:
            # Encouragement after wrong guess
            encouragements = [
                "💪 Don't give up! You're getting closer!",
                "🌟 Keep trying! You've got this!",
                "🚀 You're on the right track!",
                "✨ Great effort! Try again!",
                "🎯 You're learning! Keep going!"
            ]
            print(random.choice(encouragements))
            
            if attempt < max_attempts:
                # After first wrong guess, ask if they want hints
                if attempt == 1:
                    print("\n💡 Would you like a hint? (Ask nicely!)")
                    hint_request = input("Your request: ").strip()
                    
                    if is_polite_request(hint_request):
                        extra_hint = get_additional_hint(client, animal, shown_hints)
                        shown_hints.append(extra_hint)
                        print(f"🌟 Extra hint: {extra_hint}")
                        print("💡 That should help! You're doing great!")
                    else:
                        rude_count += 1
                        if rude_count == 1:
                            print("😊 It's better to be kind if you want to win the game! Try asking nicely.")
                            # Give them another chance
                            hint_request = input("Try again (ask nicely): ").strip()
                            if is_polite_request(hint_request):
                                extra_hint = get_additional_hint(client, animal, shown_hints)
                                shown_hints.append(extra_hint)
                                print(f"🌟 Extra hint: {extra_hint}")
                                print("💡 That should help! You're doing great!")
                            else:
                                print("😔 I'm ending this game. Please be more respectful next time!")
                                return False
                        else:
                            print("😔 I'm ending this game. Please be more respectful next time!")
                            return False
                
                print("Try again!")
                score -= penalty_per_wrong
            else:
                print("Not today. The animal was:", animal)
                print("Score: 0")
                return False


def play_game() -> None:
    client = create_client()
    print("Welcome to Crocodile! Guess the animal.")
    # Fixed category for the session
    category, _ = select_category_and_animal()
    category = category  # use chosen category; pick new animal each round

    difficulty = "easy"
    win_streak = 0

    while True:
        won = play_single_round(client, category, difficulty)
        if won:
            win_streak += 1
            if difficulty == "easy" and win_streak >= 5:
                print("You've guessed 5 in a row! Switching to Medium difficulty.")
                difficulty = "medium"
                win_streak = 0
            elif difficulty == "medium" and win_streak >= 5:
                print("You're on fire! 5 in a row at Medium. Switching to Hard difficulty.")
                difficulty = "hard"
                win_streak = 0
        else:
            # Reset streak on loss
            win_streak = 0

        # Ask to continue or quit after each round
        cont = input("Play another round? (y/n): ").strip().lower()
        if cont not in {"y", "yes"}:
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    play_game()

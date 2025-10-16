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
    difficulty_guidance = {
        "easy": "Provide a clear, fairly obvious clue a casual player could guess.",
        "medium": "Provide a balanced clue that suggests but doesn't give away.",
        "hard": "Provide a subtle, cryptic clue focusing on less-known traits.",
    }
    system_instructions = (
        "You are the Game Master for a guessing game. "
        "Produce ONE concise clue for the specified animal. Do NOT reveal the animal's name. "
        "Respond ONLY as a strict JSON object with key 'clue'."
    )
    user_prompt = (
        f"Animal: '{animal}'. Difficulty: '{difficulty}'.\n"
        f"Guidance: {difficulty_guidance.get(difficulty, '')}\n"
        "Return JSON like {\"clue\": \"I purr and love naps on sunny windowsills.\"}"
    )
    resp = client.responses.create(
        model="gpt-4o-mini",
        instructions=system_instructions,
        input=user_prompt,
    )
    text = resp.output_text.strip()
    try:
        data = json.loads(text)
        clue = str(data.get("clue", "")).strip()
        if clue:
            return clue
    except json.JSONDecodeError:
        pass
    # Fallback simple clue per difficulty
    if difficulty == "easy":
        return "This animal is well-known for its distinctive, easily recognized trait."
    if difficulty == "hard":
        return "Consider a lesser-known aspect of its behavior or anatomy."
    return "Think about where it lives and a notable behavior."


def validate_guess_with_llm(client: OpenAI, animal: str, guess: str) -> bool:
    """Ask the model if the guess matches the secret animal (allowing synonyms and case-insensitive match).
    Returns True if it's a match, False otherwise.
    """
    system_instructions = (
        "You determine whether a user's guess refers to the same animal as the secret. "
        "Consider synonyms, plural/singular, common nicknames, and case-insensitivity. "
        "Output ONLY JSON with key 'match' set to true or false."
    )

    user_prompt = (
        f"Secret animal: '{animal}'. User guess: '{guess}'.\n"
        "Respond strictly as JSON, e.g., {\"match\": true}."
    )

    resp = client.responses.create(
        model="gpt-4o-mini",
        instructions=system_instructions,
        input=user_prompt,
    )
    text = resp.output_text.strip()
    try:
        data = json.loads(text)
        match = data.get("match")
        return bool(match)
    except json.JSONDecodeError:
        # Fallback heuristic if JSON parsing failed
        normalized_animal = animal.lower().strip()
        normalized_guess = guess.lower().strip()
        return normalized_animal == normalized_guess


def get_additional_hint(client: OpenAI, animal: str, existing_hints: list[str]) -> str:
    """Ask the model for one more concise hint about the same animal.
    Ensures the hint does not repeat any in existing_hints.
    """
    system_instructions = (
        "You provide ONE extra concise hint about a secret animal. "
        "Do NOT reveal the animal name or give trivially identifying words. "
        "Avoid repeating the previous clue and focus on a different aspect (behavior, habitat, anatomy). "
        "Respond ONLY as a strict JSON object: {\"hint\": "
        "string}."
    )

    # Try up to 3 times to get a unique hint from the model
    for _ in range(3):
        user_prompt = (
            f"Secret animal (do not reveal to user): '{animal}'.\n"
            f"Already given hints (do not repeat): {json.dumps(existing_hints)}.\n"
            "Return strictly JSON like {\"hint\": \"I have stripes but am not easily domesticated.\"}"
        )

        resp = client.responses.create(
            model="gpt-4o-mini",
            instructions=system_instructions,
            input=user_prompt,
        )
        text = resp.output_text.strip()
        try:
            data = json.loads(text)
            hint = str(data.get("hint", "")).strip()
            if hint and hint not in existing_hints:
                return hint
        except json.JSONDecodeError:
            continue

    # Fallback generic non-revealing unique hint
    fallback_pool = [
        "Consider its typical habitat and a distinctive behavior.",
        "Think about its diet and how it gets food.",
        "Focus on a unique body feature that stands out.",
        "Is it more active during day or night?",
        "Consider the sounds it makes and why.",
    ]
    for candidate in fallback_pool:
        if candidate not in existing_hints:
            return candidate
    # If everything failed, return a generic line guaranteed to differ slightly
    return f"Another angle: think habitat + behavior ({random.randint(1, 9999)})."


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

    max_attempts = 5
    score = 100
    penalty_per_wrong = 20
    for attempt in range(1, max_attempts + 1):
        guess = input(f"Attempt {attempt}/{max_attempts} - Your guess: ")
        if not guess.strip():
            print("Please enter a guess.")
            continue

        is_match = validate_guess_with_llm(client, animal, guess)
        if is_match:
            print("Congratulations! You guessed it right!")
            print(f"Score: {max(score, 0)}")
            return True
        else:
            if attempt < max_attempts:
                if attempt == 3:
                    extra_hint = get_additional_hint(client, animal, shown_hints)
                    shown_hints.append(extra_hint)
                    print(f"Extra hint: {extra_hint}")
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

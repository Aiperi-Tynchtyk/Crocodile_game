## Crocodile Game (Terminal)

A terminal guessing game powered by OpenAI. The model selects an animal and gives clues; you guess the animal within 5 attempts. Difficulty promotes from Easy → Medium → Hard after 5 consecutive wins per level.

Why this README?
- Clarifies what the project does and how to use it
- Documents required environment variables (OPENAI_API_KEY)
- Provides setup/run instructions for you and collaborators
- Helps others discover features and contribute

### Features
- Categories: mammals, birds, reptiles
- Difficulties: Easy, Medium, Hard (auto-promotes after 5-streak)
- Extra hint after 3 wrong guesses (unique vs earlier hints)
- Scoring: starts 100, −20 per wrong attempt

### Requirements
- Python 3.9+
- OpenAI Python SDK (`openai`)
- An OpenAI API key set as `OPENAI_API_KEY`

### Setup
```bash
cd /Users/aiperi/Desktop/ai-cursor-demo
python3 -m venv .venv
source ./.venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install openai
```

Set your API key (temporary for current shell):
```bash
export OPENAI_API_KEY="your_real_api_key_here"
```
Or persist in `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="your_real_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Run
```bash
python crocodile.py
```
- Pick a category
- Start on Easy; win streaks promote difficulty automatically
- Guess up to 5 times; after 3 wrong guesses you’ll receive an extra hint

### Repo hygiene
- Keep secrets out of git; `.env` and `.venv` are ignored via `.gitignore`
- To push only `crocodile.py` changes:
```bash
git add crocodile.py
git commit -m "Update crocodile game"
git push
```

### Contributing
- Open issues/PRs with improvements or bug fixes
- Keep code readable; avoid committing credentials



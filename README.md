# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py 
├── tools.py                   # The three core tools
├── agent.py                   # Planning loop and session state
├── app.py                     # Gradio interface        # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

Tested by running:
```bash
python -c "
from tools import search_listings, create_fit_card
item = search_listings('vintage graphic tee', max_price=50)[0]
print(create_fit_card('', item))
"
```
Returns the error string. No exception, no LLM call.

---

## Spec Reflection

**One way the spec helped:** Writing the planning loop logic in `planning.md` before touching `agent.py` made the branching structure clear before any code existed. Knowing exactly what should happen when `search_listings` returns `[]` — set the error, return early, skip the other tools — meant there was no ambiguity when implementing it.

**One way implementation diverged from the spec:** The spec described `suggest_outfit` as having two separate prompt paths (empty wardrobe vs. populated wardrobe) that each ended with their own LLM call. During implementation, that turned into a single `if/else` block that builds the prompt, followed by one shared LLM call at the end. This was cleaner and avoided duplicating the API call — but it required making sure the `except` block wrapped the entire function, not just one branch.

---

## AI Usage

**Instance 1 — implementing `search_listings`:** I gave Claude the Tool 1 spec block from `planning.md` (inputs, return value, scoring approach, failure mode) and asked it to implement the function using `load_listings()`. The generated code filtered by price and size correctly but used a simple `in` check for keyword matching rather than scoring by overlap count. I revised it to score by the number of matching keywords across all fields and sort by that score, which produced more relevant rankings.

**Instance 2 — implementing the planning loop:** I gave Claude the Architecture diagram and Planning Loop section from `planning.md` and asked it to implement `run_agent()`. The first version called all three tools unconditionally and checked for errors after the fact. I overrode this to match the spec — early return after `search_listings` returns empty, with no further tool calls — and verified the no-results path returned `None` for `fit_card`.
# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the mock listings dataset for items that match the user's description, optional size, and optional price ceiling. Returns a ranked list of matching listings sorted by relevance score.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user wants. Matched against title, description, style_tags, category, colors, and brand.
- `size` (str): Size string to filter by, or None to skip size filtering. Case-insensitive, partial match
- `max_price` (float): Maximum price inclusive, or None to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dicts, sorted by relevance score . Each dict has: id, title , description , category , style_tags , size , condition, price , colors , brand , platform . Returns an empty list [] if nothing matches.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
The agent sets session["error"] to: "No listings found for '[description]'[size/price context]. Try a broader description, different size, or higher price limit." Then returns the session immediately — does NOT call suggest_outfit with empty input.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Uses the LLM to suggest 1–2 complete outfit combinations using the new thrifted item and pieces from the user's existing wardrobe. If the wardrobe is empty, gives general styling advice instead.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict of what items the user might buy
- `wardrobe` (dict):  A wardrobe dict with an items key containing a list of wardrobe item dicts. May have an empty items list.

**What it returns:**
<!-- Describe the return value -->
A non-empty string with outfit suggestions. If wardrobe is populated, references specific named pieces from it. If wardrobe is empty, gives general styling advice. Never returns an empty string.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the LLM call fails or returns an empty string, returns a fallback string: "This works well with basic complementary pieces. Style it with fitted or relaxed bottoms depending on the fit." Never raises an exception.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Uses the LLM to generate a short, casual, shareable 2–4 sentence caption. Mentions the item name, price, and platform naturally.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...The outfit suggestion string

**What it returns:**
<!-- Describe the return value -->
A 2–4 sentence string in casual social-media voice. Mentions the item, price, and platform once each. Sounds different for different inputs 
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
Returns a descriptive error message string. Never raises an exception.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
After initializing the session, the agent parses the query with simple regex and keyword extraction (no LLM needed — keeps it fast and predictable):
- Extract `max_price`: looks for patterns like "under $30", "less than $40", "$25 max"
- Extract `size`: looks for tokens like "size M", "size XL", or standalone size labels
- Everything remaining becomes the `description`

The conditional logic:

1. Parse query → `session["parsed"]` = `{description, size, max_price}`
2. Call `search_listings(description, size, max_price)` → if results is empty, set `session["error"]` and **return early** — `suggest_outfit` is never called with empty input
3. Set `session["selected_item"]` = `results[0]` (top relevance match)
4. Call `suggest_outfit(selected_item, wardrobe)` → store result in `session["outfit_suggestion"]`
5. Call `create_fit_card(outfit_suggestion, selected_item)` → store result in `session["fit_card"]`
6. Return session

The agent only reaches steps 4 and 5 when step 2 returns at least one result. It never calls all three tools unconditionally.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
All state lives in a single `session` dict initialized at the start of each `run_agent()` call. No values are re-entered by the user between steps — each tool reads from and writes to this shared dict.

| Field | Set by | Used by |
|-------|--------|---------|
| `query` | `run_agent` on init | parsing step |
| `parsed` | parse step | `search_listings` call |
| `search_results` | `search_listings` | selecting top item |
| `selected_item` | `run_agent` after search | `suggest_outfit`, `create_fit_card` |
| `wardrobe` | `run_agent` on init | `suggest_outfit` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card` |
| `fit_card` | `create_fit_card` | `app.py` display |
| `error` | any step on failure | `app.py` display |

The session dict is passed through the entire run and returned at the end. `app.py` reads `session["error"]` first — if set, it displays the error and leaves the other two panels empty.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | match the querySets session["error"] to a message explaining what wasn't found and suggesting adjustments (broader description, different size, higher price). Returns session early — does not proceed to suggest_outfit.|
| suggest_outfit | Wardrobe is empty | Calls LLM with a general styling prompt instead of a wardrobe-specific one. Returns general advice like "pairs well with wide-leg pants or cargo trousers for a streetwear look."|
| create_fit_card | Outfit input is missing or incomplete |Returns error string "Cannot generate fit card: outfit description is missing." without calling the LLM. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
```
User query (str)
     │
     ▼
 run_agent()
     │
     ├─ Step 1: _new_session(query, wardrobe)
     │
     ├─ Step 2: parse query → session["parsed"]
     │           {description, size, max_price}
     │
     ├─ Step 3: search_listings(description, size, max_price)
     │               │
     │         results == []?
     │               │
     │        YES ───┴──► session["error"] = "No listings found..."
     │                    RETURN session ◄─────────────────────────┐
     │        NO                                                   │
     │               │                                            │ (error path)
     │         session["search_results"] = results               │
     │         session["selected_item"]  = results[0]            │
     │               │                                            │
     ├─ Step 4: suggest_outfit(selected_item, wardrobe)          │
     │               │                                            │
     │         wardrobe empty? → general styling advice          │
     │         wardrobe populated? → specific outfit combos      │
     │               │                                            │
     │         session["outfit_suggestion"] = result             │
     │               │                                            │
     ├─ Step 5: create_fit_card(outfit_suggestion, selected_item)│
     │               │                                            │
     │         outfit empty? → return error string ──────────────┘
     │               │
     │         session["fit_card"] = caption
     │               │
     └─────────► RETURN session
```
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
search_listings: Provide Claude with the Tool 1 spec block (inputs, return value, failure mode) and ask it to implement using load_listings(). Verify: filters by all three params, handles empty results, scores by keyword overlap across title + description + style_tags + colors + brand. Test with 3 queries: one with results, one with no results, one with price filter.

suggest_outfit: Provide Claude with the Tool 2 spec block and the wardrobe_schema.json structure. Verify: handles empty wardrobe with a different prompt path, calls Groq with llama-3.3-70b-versatile, returns a non-empty string. Test with example wardrobe and empty wardrobe.

create_fit_card: Provide Claude with the Tool 3 spec block. Verify: guards against empty outfit, uses higher temperature (0.9+), output sounds casual not like a product description. Run 3 times on same input to confirm variation.
**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
Agent parses the query. Extracts: description="vintage graphic tee", size=None (no size mentioned), max_price=30.0. Stores in session["parsed"].
**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Calls search_listings("vintage graphic tee", size=None, max_price=30.0). The function loads all 40 listings, filters to those priced ≤ $30, scores each by keyword overlap with "vintage graphic tee" against title/description/style_tags. Returns e.g. [{"title": "Graphic Tee — 2003 Tour Bootleg Style", "price": 24.0, "platform": "depop", ...}, ...]. Stores in session["search_results"]. Sets session["selected_item"] = results[0].
**Step 3:**
<!-- Continue until the full interaction is complete -->
Calls suggest_outfit(selected_item, wardrobe). Wardrobe has 10 items. LLM prompt includes the tee details and the wardrobe list. Returns: "Pair this faded bootleg tee with your baggy dark wash jeans and chunky white sneakers for a classic streetwear look. Roll the sleeves once and leave it untucked. For a grungier vibe, swap the sneakers for your black combat boots and layer the vintage denim jacket over the top." Stores in session["outfit_suggestion"].

**Step 4:**
Calls create_fit_card(outfit_suggestion, selected_item). LLM generates a casual caption referencing the item, price, and platform. Returns: "thrifted this faded bootleg tee off depop for $24 and it was literally made for my wide-legs 🖤 the worn-in graphic does all the heavy lifting — full look in bio". Stores in session["fit_card"].
**Final output to user:**
<!-- What does the user actually see at the end? -->
Three panels populate in the Gradio UI — the listing details, the outfit suggestion, and the fit card caption.
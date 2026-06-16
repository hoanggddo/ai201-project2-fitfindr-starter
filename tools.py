"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    try:
        listings = load_listings()
    except Exception:
        return []
 
    # --- Step 1: filter by price ---
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]
 
    # --- Step 2: filter by size (case-insensitive, partial match) ---
    if size is not None:
        size_lower = size.lower().strip()
        listings = [
            l for l in listings
            if size_lower in l["size"].lower()
        ]
 
    # --- Step 3: score by keyword overlap ---
    keywords = set(re.sub(r"[^\w\s]", "", description.lower()).split())
 
    def score(listing: dict) -> int:
        # Build a bag of words from all searchable fields
        text_parts = [
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand", "") or "",
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]
        listing_words = set(
            re.sub(r"[^\w\s]", "", " ".join(text_parts).lower()).split()
        )
        return len(keywords & listing_words)
 
    # --- Step 4: drop zero-score results, sort by score ---
    scored = [(l, score(l)) for l in listings]
    matched = [(l, s) for l, s in scored if s > 0]
    matched.sort(key=lambda x: x[1], reverse=True)
 
    return [l for l, _ in matched]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    try:
        client = _get_groq_client()
        wardrobe_items = wardrobe.get("items", [])
 
        if not wardrobe_items:
            # Empty wardrobe — general styling advice
            prompt = f"""You are a thrift fashion stylist. A user just found this secondhand item:
 
Item: {new_item.get('title', 'Unknown item')}
Category: {new_item.get('category', '')}
Style tags: {', '.join(new_item.get('style_tags', []))}
Colors: {', '.join(new_item.get('colors', []))}
Description: {new_item.get('description', '')}
 
The user hasn't entered their wardrobe yet. Give them 1-2 paragraphs of general styling advice:
- What types of bottoms, tops, or shoes pair well with this item
- What overall aesthetic or vibe it suits
- One specific outfit idea using common wardrobe basics
 
Be specific, casual, and helpful. Don't use bullet points — write in a conversational style."""
        else:
            # Format wardrobe for the prompt
            wardrobe_lines = []
            for item in wardrobe_items:
                colors = ", ".join(item.get("colors", []))
                tags = ", ".join(item.get("style_tags", []))
                notes = item.get("notes") or ""
                line = f"- {item['name']} ({item['category']}) | colors: {colors} | style: {tags}"
                if notes:
                    line += f" | note: {notes}"
                wardrobe_lines.append(line)
 
            wardrobe_text = "\n".join(wardrobe_lines)
 
            prompt = f"""You are a thrift fashion stylist. A user just found this secondhand item:
 
            Item: {new_item.get('title', 'Unknown item')}
            Category: {new_item.get('category', '')}
            Style tags: {', '.join(new_item.get('style_tags', []))}
            Colors: {', '.join(new_item.get('colors', []))}
            Description: {new_item.get('description', '')}
            
            Their current wardrobe:
            {wardrobe_text}
            
            Suggest 1-2 complete outfit combinations using the new item and specific pieces from their wardrobe above. 
            Reference the wardrobe pieces by name. Be specific about how to style it (tucked/untucked, layering, etc.).
            Write in a casual, friendly style — 2-3 sentences per outfit. No bullet points."""
 
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7,
            )
 
            result = response.choices[0].message.content.strip()
            if not result:
                raise ValueError("Empty LLM response")
            return result
    
        except Exception as e:
            # Fallback — never crash
            category = new_item.get("category", "item")
            tags = new_item.get("style_tags", [])
            vibe = tags[0] if tags else "versatile"
            return (
                f"This {vibe} {category} works well with a range of basics. "
                f"Try pairing it with fitted or relaxed bottoms depending on the silhouette, "
                f"and finish with clean sneakers or boots to match the vibe."
            )
    


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    Returns a 2-4 sentence casual social-media style caption.
    If outfit is empty, returns an error string. Never raises an exception.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return "Cannot generate fit card: outfit description is missing."
 
    try:
        client = _get_groq_client()
 
        title = new_item.get("title", "thrifted piece")
        price = new_item.get("price", "")
        platform = new_item.get("platform", "a thrift app")
        price_str = f"${price:.0f}" if price else ""
 
        prompt = f"""Write a 2-4 sentence Instagram/TikTok caption for a thrift haul OOTD post. 
 
The thrifted item: {title} ({price_str} from {platform})
The outfit: {outfit}
 
Rules:
- Sound like a real person posting on Instagram, not a brand or product description
- Mention the item name, price, and platform naturally (once each)
- Capture the specific vibe of the outfit
- Keep it casual, a little playful — lowercase is fine, emojis are fine but don't overdo it
- 2-4 sentences max
 
Write only the caption, nothing else."""
 
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.95,  # higher temp = more variation
        )
 
        result = response.choices[0].message.content.strip()
        # Strip any surrounding quotes the LLM might add
        result = result.strip('"\'')
        if not result:
            raise ValueError("Empty LLM response")
        return result
 
    except Exception:
        title = new_item.get("title", "this find")
        price = new_item.get("price", "")
        platform = new_item.get("platform", "thrift")
        price_str = f"${price:.0f}" if price else ""
        return f"thrifted {title.lower()} {price_str} from {platform} and honestly it's everything "
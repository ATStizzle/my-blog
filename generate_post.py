#!/usr/bin/env python3
"""
Generates one new AI-written blog post using the Claude API and appends it
to posts.json. Designed to be run on a schedule (see .github/workflows/generate-post.yml).

Requires: ANTHROPIC_API_KEY environment variable.
Install deps: pip install anthropic
"""

import json
import os
import re
import sys
from datetime import date, datetime, timezone

import anthropic

POSTS_FILE = "posts.json"
MODEL = "claude-sonnet-4-6"

# Edit this to describe your site/niche/tone so posts stay on-topic.
SITE_CONTEXT = """
Business: New York Tints — a specialized compliance and documentation
service that helps New York residents obtain legal medical window tint
exemptions under New York State regulations (the MV-80W exemption
framework). The service combines pre-qualification, expert review,
process guidance, and physician-reviewed medical documentation, so
customers can keep tinted windows legally, pass state vehicle inspection,
and avoid tint-related tickets. This is New York-specific, not general
automotive tinting advice.

Brand voice: authoritative, local, and reassuring. Confident and direct,
emphasizing trust, ease, and legal protection. Removes stress and
simplifies a bureaucratic, regulated process.

Target audience: New York State vehicle owners (especially NYC and
Brooklyn) who either already have tinted windows or need darker tint due
to a qualifying medical condition (e.g. light sensitivity). They want a
fast, guided, low-friction path through a specific state exemption
process — not general legal education. They care about convenience,
legitimacy, and speed, and want to avoid inspection failures or tickets.

Service area: New York State (business is Brooklyn-based).

Key themes to draw topics from (rotate through these, don't repeat):
- New York medical window tint exemptions
- Passing NY State vehicle inspection legally
- Avoiding window tint tickets and violations
- Qualifying medical conditions for tint exemptions
- Physician-reviewed medical documentation
- Pre-qualification and streamlined application process
- New York State statute and MV-80W exemption rules
- Being a Brooklyn-based service for drivers across New York

Pick ONE specific angle/topic from these themes per post that hasn't
obviously been covered before (avoid repeating past titles below).
Do not invent specific statute numbers, medical claims, or legal
guarantees you're not certain of — keep specifics generic/directional
(e.g. "consult the official MV-80W form") rather than fabricated details.
"""


def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug[:80].strip("-")


STOPWORDS = {
    "ny", "nys", "new", "york", "medical", "window", "windows", "tint", "tinted",
    "exemption", "exemptions", "doe", "can", "you", "your", "get", "one", "for", "a",
    "an", "the", "it", "is", "do", "does", "what", "how", "if", "to", "of",
    "in", "on", "and", "or", "too", "as", "need", "happens", "with", "are",
}


def topic_words(title):
    """The meaningful words in a title, e.g. {'company', 'car'}."""
    words = re.sub(r"[^a-z0-9\s]", " ", title.lower()).split()
    words = [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words]
    return {w for w in words if w not in STOPWORDS}


def is_duplicate(title, existing_titles):
    """True if the title's topic matches or heavily overlaps any past title."""
    new_slug = slugify(title)
    new_words = topic_words(title)
    for old in existing_titles:
        if slugify(old) == new_slug:
            return True
        old_words = topic_words(old)
        if not new_words or not old_words:
            continue
        overlap = len(new_words & old_words) / len(new_words | old_words)
        if overlap >= 0.5:
            return True
    return False


def generate_post(existing_titles, rejected=None):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    # posts.json is stored newest-first, so pass ALL titles (titles are short,
    # so this costs almost nothing). The old version sent existing_titles[-30:],
    # which was the 30 OLDEST posts, so recent topics kept getting repeated.
    past_titles = "\n".join(f"- {t}" for t in existing_titles) or "(none yet)"

    rejected_note = ""
    if rejected:
        rejected_list = "\n".join(f"- {t}" for t in rejected)
        rejected_note = f"""
These titles were just REJECTED for being too similar to existing posts.
Choose a clearly different topic:
{rejected_list}
"""

    prompt = f"""{SITE_CONTEXT}

Every title already published (do NOT repeat any of these topics or angles,
even reworded):
{past_titles}
{rejected_note}
Vary the title format. Do not start the title with "NY Tint Exemption:" -
use a mix of how-to guides, checklists, myth-busting, question titles,
local Brooklyn/NYC angles, and practical tips.

Write ONE new blog post. Respond with ONLY valid JSON, no markdown fences,
no preamble, in exactly this shape:

{{
  "title": "string, 40-70 characters, SEO-friendly",
  "meta_description": "string, 120-155 characters",
  "body_html": "string, 500-900 words of HTML using <p>, <h2>, <ul>/<li> tags only, no <html>/<body> wrapper"
}}
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    text = text.strip()
    # strip accidental markdown fences just in case
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())

    data = json.loads(text)
    return data


def main():
    posts = load_posts()
    existing_titles = [p["title"] for p in posts]

    rejected = []
    data = None
    for attempt in range(3):
        try:
            candidate = generate_post(existing_titles, rejected)
        except Exception as e:
            print(f"Failed to generate post: {e}", file=sys.stderr)
            sys.exit(1)
        if is_duplicate(candidate["title"], existing_titles):
            print(f"Rejected duplicate topic: {candidate['title']}")
            rejected.append(candidate["title"])
            continue
        data = candidate
        break

    if data is None:
        # Fail the run (shows a red X in the Actions tab) instead of
        # publishing yet another repeat.
        print("Could not get a unique topic after 3 tries; nothing published.",
              file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    new_post = {
        "id": f"{date.today().isoformat()}-{slugify(data['title'])}",
        "title": data["title"],
        "meta_description": data["meta_description"],
        "body_html": data["body_html"],
        "date": now.isoformat(),
        "slug": slugify(data["title"]),
    }

    posts.insert(0, new_post)  # newest first
    save_posts(posts)
    print(f"Added post: {new_post['title']}")


if __name__ == "__main__":
    main()

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
You write blog posts for a small business website. The audience is
prospective customers doing research. Tone: clear, helpful, not salesy.
Pick a topic relevant to the business's industry that hasn't obviously
been covered before (avoid repeating past titles below).
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


def generate_post(existing_titles):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    past_titles = "\n".join(f"- {t}" for t in existing_titles[-30:]) or "(none yet)"

    prompt = f"""{SITE_CONTEXT}

Previously published titles (avoid duplicating topics):
{past_titles}

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

    try:
        data = generate_post(existing_titles)
    except Exception as e:
        print(f"Failed to generate post: {e}", file=sys.stderr)
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

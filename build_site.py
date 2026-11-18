#!/usr/bin/env python3
"""
Builds a static, Google-friendly blog from posts.json into the _site/ folder:

  _site/index.html              blog home (list of all posts)
  _site/<slug>/index.html       one real page per post
  _site/sitemap.xml             for Google Search Console
  _site/robots.txt
  _site/feed.xml                RSS feed
  _site/posts.json, widget.js   copies, so the Squarespace widget keeps working

No extra packages needed. Run locally with:  python build_site.py
The "Build and deploy blog" GitHub Action runs it automatically.
"""

import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime

# ---------------------------------------------------------------------------
# Settings — edit these if anything about the business changes.
# ---------------------------------------------------------------------------
BLOG_URL = "https://blog.nytints.com"          # no trailing slash
MAIN_SITE = "https://www.nytints.com"
GET_STARTED_URL = MAIN_SITE + "/store/p/window-tint-exemption"
FAQ_URL = MAIN_SITE + "/faqs"
BUSINESS_NAME = "New York Tints"
PHONE_DISPLAY = "(718) 968-8866"
PHONE_TEL = "+17189688866"
EMAIL = "support@nytints.com"
ADDRESS = "2108 Rockaway Parkway, Brooklyn, NY 11236"
HOURS = "Mon–Sat, 11am–6pm"
BLOG_TITLE = "New York Window Tint Exemption Blog"
BLOG_DESCRIPTION = ("Guides on New York medical window tint exemptions (MV-80W), "
                    "passing NY State inspection, and handling tint tickets — "
                    "from New York Tints in Brooklyn.")
RELATED_COUNT = 3

POSTS_FILE = "posts.json"
OUT = "_site"


def esc(s):
    return html.escape(s or "", quote=True)


def parse_date(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def nice_date(iso):
    d = parse_date(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def reading_minutes(body_html):
    words = len(re.sub(r"<[^>]+>", " ", body_html).split())
    return max(1, round(words / 220))


def post_url(post):
    return f"{BLOG_URL}/{post['slug']}/"


def jsonld(obj):
    # Escape "</" so post text can never close the script tag early.
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
            + "</script>")


CSS = """
:root{--ink:#111;--muted:#5b5b5b;--line:#e6e6e6;--bg:#fff;--soft:#f6f6f4}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--ink)}
.wrap{max-width:760px;margin:0 auto;padding:0 22px}
header.site{border-bottom:1px solid var(--line)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:16px;padding-bottom:16px;max-width:1080px}
.brand{font-weight:800;letter-spacing:.02em;text-decoration:none;font-size:19px}
nav a{margin-left:18px;text-decoration:none;font-size:15px;color:var(--muted)}
nav a:hover{color:var(--ink)}
nav a.btn{color:#fff;background:var(--ink);padding:9px 16px;border-radius:8px}
.crumbs{font-size:14px;color:var(--muted);margin:28px 0 8px}
.crumbs a{color:var(--muted)}
h1{font-size:clamp(30px,5vw,42px);line-height:1.15;margin:8px 0 12px;letter-spacing:-.01em}
.meta{color:var(--muted);font-size:15px;margin-bottom:28px}
article h2{font-size:26px;line-height:1.25;margin:40px 0 10px}
article ul{padding-left:22px}
article li{margin:6px 0}
.cta{background:var(--soft);border:1px solid var(--line);border-radius:14px;padding:26px;margin:48px 0}
.cta h2{margin:0 0 8px;font-size:24px}
.cta p{margin:0 0 16px}
.btn-lg{display:inline-block;background:var(--ink);color:#fff !important;text-decoration:none;font-weight:700;padding:13px 22px;border-radius:10px;margin:0 10px 8px 0}
.btn-ghost{display:inline-block;border:1px solid var(--ink);text-decoration:none;font-weight:700;padding:12px 20px;border-radius:10px}
.related h2{font-size:20px;margin:0 0 12px}
.card{display:block;text-decoration:none;border-top:1px solid var(--line);padding:18px 0}
.card h3{margin:0 0 4px;font-size:21px;line-height:1.3}
.card p{margin:0;color:var(--muted);font-size:16px}
.card time{font-size:14px;color:var(--muted)}
.card:hover h3{text-decoration:underline}
.intro{color:var(--muted);margin:0 0 24px}
footer.site{border-top:1px solid var(--line);margin-top:64px;padding:28px 0;font-size:15px;color:var(--muted)}
footer.site a{color:var(--muted)}
.disclaimer{font-size:13px;margin-top:12px}
@media (max-width:640px){nav a:not(.btn){display:none}}
@media (prefers-color-scheme:dark){
:root{--ink:#ECEAE6;--muted:#A9B1AF;--line:#2A3130;--bg:#121616;--soft:#1E2423}
nav a.btn,.btn-lg{background:#D4967D;color:#fff !important}
.btn-ghost{border-color:#ECEAE6;color:#ECEAE6}
}
"""


def shell(*, title, description, canonical, body, schema, og_type="website", published=None):
    extra_meta = ""
    if published:
        extra_meta = f'<meta property="article:published_time" content="{esc(published)}">\n'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:site_name" content="{esc(BUSINESS_NAME)}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
{extra_meta}<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{esc(BLOG_TITLE)}" href="{BLOG_URL}/feed.xml">
<style>{CSS}</style>
{schema}
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{MAIN_SITE}/">NEW YORK TINTS</a>
  <nav>
    <a href="{MAIN_SITE}/">Home</a>
    <a href="{FAQ_URL}">FAQ</a>
    <a href="{BLOG_URL}/">Blog</a>
    <a class="btn" href="{GET_STARTED_URL}">Get Started</a>
  </nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
  <strong>{esc(BUSINESS_NAME)}</strong> · {esc(ADDRESS)}<br>
  <a href="tel:{PHONE_TEL}">{esc(PHONE_DISPLAY)}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a> · {esc(HOURS)}<br>
  Helping drivers across New York State get medical window tint exemptions.
  <p class="disclaimer">Articles are general information, not legal or medical advice.
  Eligibility is determined by a physician and approval by the NYS DMV.</p>
</div></footer>
</body>
</html>
"""


BUSINESS_SCHEMA = {
    "@type": "LocalBusiness",
    "@id": MAIN_SITE + "/#business",
    "name": BUSINESS_NAME,
    "url": MAIN_SITE + "/",
    "telephone": PHONE_TEL,
}


def cta_block():
    return f"""<section class="cta">
  <h2>Think you might qualify?</h2>
  <p>New York Tints handles the physician review and MV-80W paperwork so you can keep your tint legally and pass inspection. Brooklyn-based, serving all of New York State.</p>
  <a class="btn-lg" href="{GET_STARTED_URL}">Get Started</a>
  <a class="btn-ghost" href="tel:{PHONE_TEL}">Call {esc(PHONE_DISPLAY)}</a>
</section>"""


def card(p):
    return (f'<a class="card" href="{post_url(p)}">'
            f'<time datetime="{esc(p["date"])}">{nice_date(p["date"])}</time>'
            f'<h3>{esc(p["title"])}</h3><p>{esc(p["meta_description"])}</p></a>')


def build_post(post, related):
    url = post_url(post)
    schema = jsonld({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "headline": post["title"],
                "description": post["meta_description"],
                "datePublished": post["date"],
                "dateModified": post.get("updated", post["date"]),
                "mainEntityOfPage": url,
                "url": url,
                "author": {"@type": "Organization", "name": BUSINESS_NAME, "url": MAIN_SITE + "/"},
                "publisher": BUSINESS_SCHEMA,
                "inLanguage": "en-US",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": MAIN_SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Blog", "item": BLOG_URL + "/"},
                    {"@type": "ListItem", "position": 3, "name": post["title"], "item": url},
                ],
            },
        ],
    })
    rel = "".join(card(p) for p in related)
    body = f"""<div class="crumbs"><a href="{MAIN_SITE}/">Home</a> › <a href="{BLOG_URL}/">Blog</a></div>
<article>
<h1>{esc(post["title"])}</h1>
<div class="meta"><time datetime="{esc(post["date"])}">{nice_date(post["date"])}</time> · {reading_minutes(post["body_html"])} min read · {esc(BUSINESS_NAME)}</div>
{post["body_html"]}
</article>
{cta_block()}
<section class="related"><h2>Keep reading</h2>{rel}</section>"""
    return shell(title=f'{post["title"]} | {BUSINESS_NAME}',
                 description=post["meta_description"], canonical=url, body=body,
                 schema=schema, og_type="article", published=post["date"])


def build_index(posts):
    schema = jsonld({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": BLOG_TITLE,
        "url": BLOG_URL + "/",
        "description": BLOG_DESCRIPTION,
        "publisher": BUSINESS_SCHEMA,
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": post_url(p),
                      "datePublished": p["date"]} for p in posts],
    })
    body = f"""<div class="crumbs"><a href="{MAIN_SITE}/">Home</a> › Blog</div>
<h1>{esc(BLOG_TITLE)}</h1>
<p class="intro">{esc(BLOG_DESCRIPTION)}</p>
{"".join(card(p) for p in posts)}
{cta_block()}"""
    return shell(title=f"{BLOG_TITLE} | {BUSINESS_NAME}", description=BLOG_DESCRIPTION,
                 canonical=BLOG_URL + "/", body=body, schema=schema)


def build_sitemap(posts):
    newest = posts[0]["date"] if posts else datetime.now(timezone.utc).isoformat()
    urls = [f"<url><loc>{BLOG_URL}/</loc><lastmod>{newest[:10]}</lastmod></url>"]
    urls += [f"<url><loc>{post_url(p)}</loc><lastmod>{p.get('updated', p['date'])[:10]}</lastmod></url>"
             for p in posts]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def build_feed(posts):
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{post_url(p)}</link>"
        f"<guid>{post_url(p)}</guid><pubDate>{format_datetime(parse_date(p['date']))}</pubDate>"
        f"<description>{esc(p['meta_description'])}</description></item>"
        for p in posts[:20])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{esc(BLOG_TITLE)}</title><link>{BLOG_URL}/</link>"
            f"<description>{esc(BLOG_DESCRIPTION)}</description>{items}</channel></rss>\n")


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    with open(POSTS_FILE, encoding="utf-8") as f:
        posts = json.load(f)

    # Make sure every post has a unique slug.
    seen = set()
    for p in posts:
        base = p["slug"]
        slug, n = base, 2
        while slug in seen:
            slug, n = f"{base}-{n}", n + 1
        p["slug"] = slug
        seen.add(slug)

    posts.sort(key=lambda p: p["date"], reverse=True)

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    for i, p in enumerate(posts):
        others = posts[i + 1:] + posts[:i]  # older posts first, then wrap around
        write(f"{OUT}/{p['slug']}/index.html", build_post(p, others[:RELATED_COUNT]))

    write(f"{OUT}/index.html", build_index(posts))
    write(f"{OUT}/sitemap.xml", build_sitemap(posts))
    write(f"{OUT}/feed.xml", build_feed(posts))
    write(f"{OUT}/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BLOG_URL}/sitemap.xml\n")
    write(f"{OUT}/404.html", shell(
        title=f"Page not found | {BUSINESS_NAME}", description=BLOG_DESCRIPTION,
        canonical=BLOG_URL + "/", schema="",
        body=f'<h1>Page not found</h1><p><a href="{BLOG_URL}/">Browse all articles →</a></p>'))

    # posts.json for the Squarespace widget, with each post's page URL added.
    with_urls = [dict(p, url=post_url(p)) for p in posts]
    write(f"{OUT}/posts.json", json.dumps(with_urls, indent=2, ensure_ascii=False))
    shutil.copy("widget.js", f"{OUT}/widget.js")

    print(f"Built {len(posts)} post pages into {OUT}/")


if __name__ == "__main__":
    main()

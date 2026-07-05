# Self-hosted AI blog (replaces Soro)

Total ongoing cost: a few cents per post in Claude API usage. No monthly fee.

## How it works
- `generate_post.py` calls the Claude API and writes a new post into `posts.json`.
- A GitHub Actions workflow runs that script on a schedule (e.g. weekly) and commits the update — nothing needs to run on your own machine.
- GitHub Pages serves `posts.json` and `widget.js` for free.
- On your Squarespace page, the `<div id="soro-blog">` + a `<script>` tag (pointing at your `widget.js` instead of Soro's) fetches `posts.json` and renders the posts — same pattern Soro used.

## Setup (about 15 minutes)

1. **Create a GitHub repo** (public repo — needed for free GitHub Pages) and push these files into it.

2. **Add your Anthropic API key as a secret**:
   Repo → Settings → Secrets and variables → Actions → New repository secret
   Name: `ANTHROPIC_API_KEY`, value: your key from console.anthropic.com

3. **Enable GitHub Pages**:
   Repo → Settings → Pages → Source: "Deploy from a branch" → branch `main`, folder `/ (root)`.
   Your files will be served at `https://YOUR-USERNAME.github.io/YOUR-REPO/`.

4. **Edit `widget.js`**: set `POSTS_URL` to
   `https://YOUR-USERNAME.github.io/YOUR-REPO/posts.json`
   (replace with your actual username/repo), commit and push.

5. **Generate your first post manually** (don't wait for the weekly cron):
   Repo → Actions tab → "Generate blog post" workflow → "Run workflow" button.
   Check that `posts.json` gets a commit with your first post.

6. **Update your Squarespace code block.** Replace:
   ```html
   <script src="https://app.trysoro.com/api/embed/6e2293c6-5244-4b62-b2e1-031fc8376dbd" defer></script>
   ```
   with:
   ```html
   <script src="https://YOUR-USERNAME.github.io/YOUR-REPO/widget.js" defer></script>
   ```
   Keep the `<div id="soro-blog"></div>` above it — that part doesn't change.

7. **Adjust the schedule** in `.github/workflows/generate-post.yml` if you want more/fewer posts per month (the cron line). [crontab.guru](https://crontab.guru) helps write the schedule.

8. **Style it**: `widget.js` renders plain `<article>` elements with class names like `ai-blog-post`, `ai-blog-title`, etc. Add CSS for those classes in your Squarespace site's custom CSS (Design → Custom CSS) to match your site's look.

## Customizing what it writes about
Edit the `SITE_CONTEXT` string near the top of `generate_post.py` — describe your business, niche, and tone. The script also feeds in your past post titles so it doesn't repeat topics.

## Costs
- GitHub Actions: free for public repos (2,000 min/month free tier, this uses under a minute per run).
- GitHub Pages: free.
- Claude API: pay-per-token, typically a few cents per ~700-word post.

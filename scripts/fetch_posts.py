import json
import datetime
import requests

# --- Load config ---
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

keywords = config.get("keywords", [])
sources = config.get("sources", {})

# --- Prepare storage ---
data_file = "data.json"
try:
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"last_updated": "", "posts": []}

new_posts = []

# --- Helper: check duplicate ---
existing_ids = {p["id"] for p in data.get("posts", [])}

# --- Fetch from Bluesky ---
if sources.get("bluesky"):
    for kw in keywords:
        try:
            r = requests.get(
                f"https://bsky.social/api/v1/search/posts?query={kw}&limit=10"
            )
            if r.status_code == 200:
                for post in r.json().get("posts", []):
                    pid = post.get("postId") or post.get("uri")
                    if pid not in existing_ids:
                        new_posts.append({
                            "id": pid,
                            "source": "bluesky",
                            "text": post.get("text",""),
                            "url": f"https://bsky.app/profile/{post.get('author','')}/post/{post.get('postId','')}",
                            "date": post.get("indexedAt","")
                        })
        except Exception as e:
            print("Bluesky error:", e)

# --- Fetch from Mastodon ---
if sources.get("mastodon"):
    # مثال على instance mastodon
    instances = ["mastodon.social", "mas.to"]
    for inst in instances:
        for kw in keywords:
            try:
                r = requests.get(
                    f"https://{inst}/api/v2/search?q={kw}&type=statuses&limit=5"
                )
                if r.status_code == 200:
                    for post in r.json().get("statuses", []):
                        pid = post.get("id")
                        if pid not in existing_ids:
                            new_posts.append({
                                "id": pid,
                                "source": f"mastodon:{inst}",
                                "text": post.get("content",""),
                                "url": post.get("url",""),
                                "date": post.get("created_at","")
                            })
            except Exception as e:
                print(f"Mastodon {inst} error:", e)

# --- Merge & Sort by date descending ---
all_posts = new_posts + data.get("posts", [])
all_posts.sort(key=lambda x: x.get("date",""), reverse=True)

# --- Keep last 200 posts max ---
all_posts = all_posts[:200]

# --- Save ---
data = {
    "last_updated": datetime.datetime.utcnow().isoformat(),
    "posts": all_posts
}
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fetched {len(new_posts)} new posts. Total stored: {len(all_posts)}")

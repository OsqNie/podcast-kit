#!/usr/bin/env python3
"""Build the podcast RSS feed (feed.xml) from episodes/*.mp3 using Dropbox shared links.

Show details come from show.json; Dropbox credentials from .env. Standard library only.

  python3 publish.py --auth        one-time: get a Dropbox refresh token for .env
  python3 publish.py               rebuild feed.xml (creates links for new MP3s and cover.jpg)
  python3 publish.py --feed-link   same, then print the feed URL to add to a podcast app

.env keys: DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
Dropbox app permissions needed: files.metadata.read, sharing.read, sharing.write
"""
import email.utils
import html
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
EPISODES = HERE / "episodes"
LINKS_CACHE = HERE / ".links.json"


class LinkExists(Exception):
    pass


def load_env():
    env = {}
    path = HERE / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def post(url, data, headers=None, form=False):
    body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
    hdrs = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        if "shared_link_already_exists" in detail:
            raise LinkExists() from None
        sys.exit(f"Dropbox API error {e.code} at {url.rsplit('/', 2)[-2:]}:\n{detail}")


def auth(env):
    key, secret = env.get("DROPBOX_APP_KEY"), env.get("DROPBOX_APP_SECRET")
    if not key or not secret:
        sys.exit("Add DROPBOX_APP_KEY and DROPBOX_APP_SECRET to .env first.")
    print("Open this URL, allow access, and paste the code here:\n")
    print(f"https://www.dropbox.com/oauth2/authorize?client_id={key}&response_type=code&token_access_type=offline\n")
    code = input("Code: ").strip()
    tok = post("https://api.dropboxapi.com/oauth2/token",
               {"code": code, "grant_type": "authorization_code", "client_id": key, "client_secret": secret}, form=True)
    print("\nAdd this line to .env:\nDROPBOX_REFRESH_TOKEN=" + tok["refresh_token"])


def access_token(env):
    if not env.get("DROPBOX_REFRESH_TOKEN"):
        sys.exit("DROPBOX_REFRESH_TOKEN missing from .env (run: python3 publish.py --auth)")
    tok = post("https://api.dropboxapi.com/oauth2/token",
               {"grant_type": "refresh_token", "refresh_token": env["DROPBOX_REFRESH_TOKEN"],
                "client_id": env["DROPBOX_APP_KEY"], "client_secret": env["DROPBOX_APP_SECRET"]}, form=True)
    return tok["access_token"]


def raw_url(url):
    parts = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(parts.query))
    q.pop("dl", None)
    q["raw"] = "1"  # serve the file itself, not Dropbox's preview page
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


def shared_link(token, path):
    auth_h = {"Authorization": f"Bearer {token}"}
    try:
        url = post("https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings", {"path": path}, auth_h)["url"]
    except LinkExists:
        url = post("https://api.dropboxapi.com/2/sharing/list_shared_links",
                   {"path": path, "direct_only": True}, auth_h)["links"][0]["url"]
    return raw_url(url)


def describe(mp3):
    txt = mp3.with_suffix(".txt")
    paras = [p.strip() for p in txt.read_text(encoding="utf-8").split("\n\n") if p.strip()] if txt.exists() else []
    summary = paras[1] if len(paras) > 1 else (paras[0] if paras else "")  # first paragraph is the greeting
    return summary, "\n\n".join(paras)


def main():
    env = load_env()
    if "--auth" in sys.argv:
        return auth(env)
    show = json.loads((HERE / "show.json").read_text(encoding="utf-8"))
    title = show.get("title", "Podcast")
    base = show.get("dropbox_base", "").rstrip("/")
    if not base:
        sys.exit("Set dropbox_base in show.json (this folder's path inside Dropbox, e.g. /Podcasts/My Show)")
    tz = ZoneInfo(show.get("timezone", "Europe/Helsinki"))
    keep = int(show.get("keep_episodes", 30))
    include_script = show.get("include_script_in_feed", True)

    cache = json.loads(LINKS_CACHE.read_text()) if LINKS_CACHE.exists() else {}
    token = None

    def link(name, path):
        nonlocal token
        if name not in cache:
            token = token or access_token(env)
            cache[name] = shared_link(token, path)
        return cache[name]

    items = []
    for mp3 in sorted(EPISODES.glob("*.mp3"), reverse=True)[:keep]:
        url = link(mp3.name, f"{base}/episodes/{mp3.name}")
        size = mp3.stat().st_size
        try:
            day = datetime.strptime(mp3.stem[:10], "%Y-%m-%d").date()
            pub = datetime.combine(day, time(6, 30), tz)
        except ValueError:
            pub = datetime.fromtimestamp(mp3.stat().st_mtime, timezone.utc)
        summary, full = describe(mp3)
        body = f"\n      <content:encoded><![CDATA[{full.replace(']]>', ']] >')}]]></content:encoded>" if include_script else ""
        items.append(f"""    <item>
      <title>{html.escape(title)} {pub.day}.{pub.month}.{pub.year}</title>
      <guid isPermaLink="false">{html.escape(title)}-{html.escape(mp3.stem)}</guid>
      <pubDate>{email.utils.format_datetime(pub)}</pubDate>
      <description>{html.escape(summary)}</description>{body}
      <enclosure url="{html.escape(url)}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{int(size * 8 / 128000)}</itunes:duration>
    </item>""")

    image = ""
    if (HERE / "cover.jpg").exists():
        u = html.escape(link("cover.jpg", f"{base}/cover.jpg"))
        image = (f'    <itunes:image href="{u}"/>\n'
                 f'    <image><url>{u}</url><title>{html.escape(title)}</title><link>https://www.dropbox.com</link></image>\n')
    LINKS_CACHE.write_text(json.dumps(cache, indent=1))

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:podcast="https://podcastindex.org/namespace/1.0">
  <channel>
    <title>{html.escape(title)}</title>
    <description>{html.escape(show.get("description", ""))}</description>
    <language>{html.escape(show.get("language", "en"))}</language>
    <itunes:author>{html.escape(show.get("author", ""))}</itunes:author>
    <itunes:block>Yes</itunes:block>
    <podcast:block>yes</podcast:block>
{image}    <itunes:explicit>false</itunes:explicit>
    <lastBuildDate>{email.utils.format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (HERE / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"feed.xml: {len(items)} episode(s)")
    if "--feed-link" in sys.argv:
        print("Feed URL:", shared_link(token or access_token(env), f"{base}/feed.xml"))


if __name__ == "__main__":
    main()

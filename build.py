#!/usr/bin/env python3
"""Builds the DJ Berry website from the files in ./content into ./site.
Netlify runs this automatically on every change (see netlify.toml)."""
import json, os, shutil, html, datetime, re
import yaml

C = lambda f: yaml.safe_load(open(os.path.join("content", f), encoding="utf-8")) or []
S = C("site.yml"); EVENTS = C("events.yml"); RELEASES = C("releases.yml"); PLAYLISTS = C("playlists.yml"); VENUES = C("venues.yml"); MIXES = C("mixes.yml")
SITE = S["domain"].rstrip("/")
OUT = "site"
TODAY = datetime.date.today().isoformat()
L = S["links"]
SAME_AS = [u for u in L.values() if u]
IG = L["instagram"]; WA = "https://wa.me/" + re.sub(r"\D", "", S["whatsapp"])
EMAIL = S["email"]
GENRES = S["genres"]
e = lambda s: html.escape(str(s or ""), quote=True)

def spotify_id(url, kind):
    m = re.search(rf"open\.spotify\.com/(?:intl-\w+/)?{kind}/([A-Za-z0-9]+)", url or "")
    return m.group(1) if m else None

def nice_date(d):
    try: return datetime.date.fromisoformat(d)
    except Exception: return None

UPCOMING = sorted([ev for ev in EVENTS if (ev.get("date") or "") >= TODAY], key=lambda x: (x["date"], x.get("time") or ""))

# ---------- Structured data ----------
PERSON = {
    "@type": "Person", "@id": f"{SITE}/#berrylinn", "name": S["artist_name"],
    "alternateName": [S["stage_name"], "Berry", "DJ Berry Bangkok", "Berry Linn DJ"],
    "jobTitle": ["DJ", "Music Producer"], "gender": "Female", "description": S["short_bio"],
    "url": f"{SITE}/", "image": f"{SITE}/images/dj-berry-berry-linn-portrait-bangkok.jpg",
    "homeLocation": {"@type": "Place", "name": S["based_in"]},
    "nationality": {"@type": "Country", "name": S["from"]},
    "knowsAbout": GENRES + ["DJing", "Music production"],
    "memberOf": {"@type": "Organization", "name": "Deep House Thailand", "url": "https://deephousethailand.com/"},
    "email": f"mailto:{EMAIL}", "sameAs": SAME_AS,
}
ARTIST = {
    "@type": "MusicGroup", "@id": f"{SITE}/#djberry", "name": S["stage_name"], "alternateName": [S["artist_name"], "Berry"],
    "genre": GENRES, "foundingLocation": {"@type": "Place", "name": S["based_in"]}, "url": f"{SITE}/",
    "image": f"{SITE}/images/dj-berry-berry-linn-portrait-bangkok.jpg",
    "member": {"@id": f"{SITE}/#berrylinn"}, "sameAs": SAME_AS,
    "track": [{"@type": "MusicRecording", "name": r["title"], "url": r.get("spotify_url") or None,
               "byArtist": {"@id": f"{SITE}/#djberry"}} for r in RELEASES] + [{"@type": "MusicRecording", "name": f"{m['title']} (DJ mix)", "url": m["url"], "byArtist": {"@id": f"{SITE}/#djberry"}} for m in (yaml.safe_load(open("content/mixes.yml")) or [])],
}
WEBSITE = {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "DJ Berry — Berry Linn",
           "inLanguage": "en", "publisher": {"@id": f"{SITE}/#berrylinn"}}

def event_schema(ev):
    start = ev["date"] + (f"T{ev['time']}:00+07:00" if ev.get("time") else "")
    d = {"@type": "MusicEvent", "name": ev["name"], "startDate": start,
         "eventStatus": "https://schema.org/EventScheduled",
         "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
         "location": {"@type": "Place", "name": ev["venue"], "address": {"@type": "PostalAddress",
                      "streetAddress": ev.get("address") or None, "addressLocality": ev.get("city"), "addressCountry": ev.get("country", "Thailand")}},
         "performer": {"@id": f"{SITE}/#djberry"}, "organizer": {"@type": "Organization", "name": ev["venue"]},
         "image": f"{SITE}{ev['poster']}" if ev.get("poster") else f"{SITE}/images/og-dj-berry.jpg",
         "description": f"DJ Berry plays {ev['name']} at {ev['venue']}, {ev.get('city')}."}
    if ev.get("ticket_url"):
        d["offers"] = {"@type": "Offer", "url": ev["ticket_url"], "availability": "https://schema.org/InStock"}
    return d

def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}

def faq_html(items):
    return "\n".join(f'<details{" open" if i == 0 else ""}><summary>{e(q)}</summary><p>{e(a)}</p></details>' for i, (q, a) in enumerate(items))

# ---------- Shared pieces ----------
NAV = [("/music/", "Music"), ("/events/", "Events"), ("/about/", "About"), ("/press-kit/", "Press kit"), ("/book-dj/", "Book Berry")]

def page(path, title, desc, crumb, body, schema=(), og_type="website", image="/images/og-dj-berry.jpg", noindex=False):
    graph = [PERSON, ARTIST, WEBSITE, {"@type": "WebPage", "@id": f"{SITE}{path}#page", "url": f"{SITE}{path}", "name": title,
             "description": desc, "isPartOf": {"@id": f"{SITE}/#website"}, "about": {"@id": f"{SITE}/#berrylinn"}, "dateModified": TODAY}]
    if path != "/":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": crumb, "item": f"{SITE}{path}"}]})
        body = body.replace("{{CRUMBS}}", f'<p class="crumbs"><a href="/">Home</a> / {e(crumb)}</p>')
    graph += list(schema)
    nav = "".join(
        f'<li class="{"pill keep" if href == "/book-dj/" else ""}"><a href="{href}"' + (' aria-current="page"' if href == path else "") + f'>{label}</a></li>'
        for href, label in NAV)
    social = " ".join(f'<a href="{u}" target="_blank" rel="me noopener">{n}</a>' for n, u in
                      [("Instagram", IG), ("Spotify", L["spotify"]), ("SoundCloud", L["soundcloud"]), ("Bandsintown", L["bandsintown"]),
                       ("Facebook", L["facebook"]), ("YouTube", L["youtube"]), ("TikTok", L["tiktok"]), ("Resident Advisor", L["resident_advisor"])] if u)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta name="robots" content="{"noindex" if noindex else "index, follow, max-image-preview:large"}">
<meta name="author" content="Berry Linn (DJ Berry)">
<meta name="theme-color" content="#0D0C0C">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="DJ Berry — Berry Linn">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{image}">
<meta property="og:image:alt" content="Berry Linn (DJ Berry), Bangkok-based DJ and music producer">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@700;800&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">
{json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=1, ensure_ascii=False)}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <a class="logo" href="/" aria-label="DJ Berry home">BERRY<span class="dot">.</span></a>
  <nav aria-label="Main"><ul class="nav">{nav}</ul></nav>
</div></header>
<main id="main">
{body}
</main>
<footer><div class="wrap">
  <p class="big" aria-hidden="true">BERRY<span class="dot">.</span></p>
  <div class="cols">
    <span>© {datetime.date.today().year} Berry Linn · DJ Berry · DJ &amp; Music Producer · {e(S["based_in"])} · Available worldwide</span>
    <span class="links">{social}</span>
  </div>
</div></footer>
<script src="/site.js" defer></script>
</body>
</html>
"""
    target = os.path.join(OUT, "404.html") if path == "/404" else os.path.join(OUT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    open(target, "w", encoding="utf-8").write(doc)

def events_list(evts, limit=None):
    if not evts:
        return f'<p class="empty">New dates are announced first on <a href="{IG}" target="_blank" rel="noopener">Instagram @berry_linn</a> and <a href="{L["bandsintown"]}" target="_blank" rel="noopener">Bandsintown</a>.</p>'
    items = []
    for ev in evts[:limit]:
        d = nice_date(ev["date"])
        day = d.strftime("%d %b") if d else e(ev["date"])
        wk = d.strftime("%a") + (f" · {ev['time']}" if ev.get("time") else "") if d else ""
        btn = f'<a class="btn small red" href="{e(ev["ticket_url"])}" target="_blank" rel="noopener">Tickets</a>' if ev.get("ticket_url") else '<span class="label">Free / at the door</span>' if ev.get("free") else ""
        items.append(f'''<li class="event" data-date="{e(ev["date"])}">
  <time datetime="{e(ev["date"])}">{day}<small>{e(wk)}</small></time>
  <div><h3>{e(ev["name"])}</h3><p>{e(ev["venue"])} · {e(ev.get("city"))}{(" · " + e(ev["lineup"])) if ev.get("lineup") else ""}</p></div>
  {btn}
</li>''')
    return f'<ul class="events">{"".join(items)}</ul>'

def release_cards():
    out = []
    for i, r in enumerate(RELEASES):
        sid = spotify_id(r.get("spotify_url"), "track")
        embed = f'<iframe class="embed" title="Listen to {e(r["title"])} on Spotify" src="https://open.spotify.com/embed/track/{sid}?utm_source=generator&amp;theme=0" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>' if sid else ""
        cover = f'<div class="cover"><img src="{e(r["cover"])}" alt="{e(r["title"])} single cover — {e(r.get("credit"))}" width="96" height="96" loading="lazy"><p>{e(r.get("description"))}</p></div>' if r.get("cover") else f'<p>{e(r.get("description"))}</p>'
        out.append(f'''<article class="release{" feature" if i == 0 else ""}">
  <span class="label">{e(r.get("type"))} · {e(r.get("credit"))}{(" · " + e(r["date"])) if r.get("date") else ""}</span>
  <h3>{e(r["title"])}</h3>
  {cover}
  {embed}
  {f'<a class="btn small" href="{e(r["spotify_url"])}" target="_blank" rel="noopener">Listen on Spotify</a>' if r.get("spotify_url") else ""}
</article>''')
    return f'<div class="releases">{"".join(out)}</div>'

from urllib.parse import quote
def mix_cards(limit=None):
    out = []
    for m in MIXES[:limit]:
        src = "https://w.soundcloud.com/player/?url=" + quote(m["url"], safe="") + "&amp;color=%23ff3b1f&amp;auto_play=false&amp;hide_related=true&amp;show_comments=false&amp;show_user=true&amp;show_reposts=false&amp;show_teaser=false"
        out.append(f'''<article class="release mix"><span class="label">DJ mix · SoundCloud</span>
  <h3 style="font-size:clamp(26px,2.6vw,36px)">{e(m["title"])}</h3><p>{e(m.get("description"))}</p>
  <iframe class="embed" style="height:166px;border-radius:4px" title="{e(m["title"])} — DJ Berry on SoundCloud" src="{src}" loading="lazy" allow="autoplay"></iframe>
  <a class="btn small" href="{e(m["url"])}" target="_blank" rel="noopener">Open on SoundCloud</a></article>''')
    return f'<div class="releases">{"".join(out)}</div>'

def venues_html():
    cols = []
    for g in VENUES:
        lis = "".join(f'<li>{"<b>" + e(v["name"]) + "</b>" if v.get("highlight") else e(v["name"])}<span>{e(v.get("note"))}</span></li>' for v in g["items"])
        cols.append(f'<div><h3>{e(g["group"])}</h3><ul>{lis}</ul></div>')
    return f'<div class="venues">{"".join(cols)}</div>'

chips = lambda items: '<ul class="chips">' + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"
stats = '<div class="stats">' + "".join(f'<div><b>{e(s["value"]).replace("+", "<i>+</i>")}</b><span class="label">{e(s["label"])}</span></div>' for s in S["stats"]) + "</div>"
countries = " · ".join(S["countries"])

def book_cta(h="Book Berry<span class=\"dot\">.</span>", text="Available for clubs, festivals, private events and tours across Asia, Europe and worldwide. Get in touch for dates, fees and travel."):
    return f'''<section id="book"><div class="wrap split">
  <div><p class="label">Bookings</p><h2 class="h2">{h}</h2><p class="lead" style="margin-top:22px;max-width:44ch">{text}</p>
  <div class="row" style="margin-top:26px"><a class="btn red" href="/book-dj/">Send a booking request</a></div></div>
  <div class="contact"><dl>
    <div><dt>Email</dt><dd class="red"><a href="mailto:{EMAIL}">{EMAIL}</a></dd></div>
    <div><dt>WhatsApp</dt><dd><a href="{WA}" target="_blank" rel="noopener">{e(S["whatsapp"])}</a></dd></div>
    <div><dt>Instagram</dt><dd><a href="{IG}" target="_blank" rel="noopener">@berry_linn</a></dd></div>
    <div><dt>Based in</dt><dd>{e(S["based_in"])} · Available worldwide</dd></div>
  </dl></div>
</div></section>'''

IMG = lambda f, alt, cls="", lazy=True, w=1600, h=1067: f'<figure class="{cls}"><img src="/images/{f}" alt="{e(alt)}" width="{w}" height="{h}"{" loading=lazy" if lazy else ""}></figure>'

GALLERY = f'''<div class="gallery">
  {IMG("dj-berry-live-bangkok-club-crowd.jpg", "DJ Berry playing a house music set to a packed club crowd in Bangkok", "g-a")}
  {IMG("dj-berry-shelter-phuket-house-techno.jpg", "DJ Berry behind the decks at Shelter, a house and techno night in Phuket", "g-b", w=1440, h=1440)}
  {IMG("dj-berry-festival-live-set.jpg", "DJ Berry in headphones playing a live festival set under purple lights", "g-c")}
  {IMG("dj-berry-dj-set-no-more-snow.jpg", "DJ Berry in a wide-brim hat mixing on Pioneer CDJs", "g-d")}
  {IMG("dj-berry-outdoor-night-set-thailand.jpg", "DJ Berry playing an outdoor night set in Thailand under red lights", "g-e", w=1265, h=1581)}
</div>'''

# ================= HOME =================
HOME_FAQ = [
    ("Who is DJ Berry?", S["short_bio"]),
    ("What music does DJ Berry play?", "House, tech house, afro house, indie dance, minimal, disco, techno and acid. Berry blends moods rather than switching genres, moving from warm, groovy sets to dark, hypnotic techno when the night asks for it."),
    ("Is DJ Berry also a music producer?", "Yes. Berry released her debut single \"SACHI\" (Berry ft. BYAS) in March 2026, followed by \"24 Turn It Up\". Both are on Spotify and all streaming platforms."),
    ("Where has DJ Berry played?", "Wonderfruit, Sing Sing Theater, Mustache Bangkok, Baccarat, APT 101, MU:IN, Full Moon Festival, UOB Live and many more, across Thailand, Myanmar, India, Sri Lanka, Singapore, Vietnam and the Philippines."),
    ("How do I book DJ Berry?", f"Email {EMAIL}, message WhatsApp {S['whatsapp']}, or send a request at berrylinnmusic.com/book-dj. Berry is based in Bangkok and available for bookings worldwide."),
]
page("/", "DJ Berry — Bangkok-Based DJ & Music Producer | Berry Linn",
     "DJ Berry (Berry Linn) is a Bangkok-based female DJ and music producer from Myanmar playing house, tech house, afro house and techno. Debut single SACHI out now. Bookings worldwide.",
     "Home", f'''
<div class="wrap hero">
  <div>
    <p class="label">DJ &amp; Producer · {e(S["based_in"])} · Booking worldwide</p>
    <h1><span class="wordmark">BERRY<span class="dot">.</span></span><span class="h1-sub">DJ Berry — Bangkok-Based DJ &amp; Music Producer</span></h1>
    <p class="tag">{e(S["tagline"])}</p>
    <p class="genres">{" · ".join(GENRES[:4])} · Techno</p>
    <div class="row"><a class="btn red" href="/book-dj/">Book Berry</a><a class="btn" href="/music/">Listen to SACHI</a></div>
  </div>
  <figure>
    <img src="/images/dj-berry-berry-linn-portrait-bangkok.jpg" alt="Portrait of Berry Linn (DJ Berry), Bangkok-based DJ and music producer" width="1600" height="1600" fetchpriority="high">
    <a class="chip" href="/music/">New single · SACHI</a>
  </figure>
</div>

<section id="dates"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Upcoming</p><h2>Next up<span class="dot">.</span></h2></div><a class="btn small" href="/events/">All events</a></div>
  {events_list(UPCOMING, 4)}
</div></section>

<section id="music"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Music · Producer</p><h2>Out now<span class="dot">.</span></h2></div><a class="btn small" href="/music/">Music &amp; playlists</a></div>
  {release_cards()}
</div></section>

<section id="mixes"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Music · DJ</p><h2>Live DJ sets<span class="dot">.</span></h2></div><a class="btn small" href="{L["soundcloud"]}" target="_blank" rel="noopener">All mixes on SoundCloud</a></div>
  {mix_cards()}
</div></section>

<section id="about"><div class="wrap split">
  <div><p class="label red">About</p><h2 class="h2">Slightly dangerous <span class="dot">behind the decks.</span></h2></div>
  <div class="prose">
    <p class="lead">Berry Linn, known on the decks as <strong>DJ Berry</strong>, is a Bangkok-based house and techno DJ and music producer with five years of professional performance behind her and a debut release out in 2026.</p>
    <p>One of the early names in <strong>Myanmar's electronic music scene</strong>, Berry took her sound on the road across India, Sri Lanka, Singapore, Vietnam, the Philippines and Thailand. Now rooted in Bangkok, she has played <strong>Wonderfruit, Sing Sing Theater, Mustache Bangkok, Baccarat, APT 101 and MU:IN</strong>, and is part of the <strong>Deep House Thailand</strong> lineup.</p>
    <p><a class="btn small" href="/about/">Read Berry's story</a></p>
    {stats}
  </div>
</div></section>

<section id="sound"><div class="wrap split">
  <div><p class="label red">The sound</p><blockquote class="pull">“{e(S["quote_sound"])}”</blockquote></div>
  <div class="prose"><p>Berry moves freely between funky jazz grooves, disco energy, afro house rhythms, indie dance attitude and minimal tech house precision, then into progressive techno tension, acid and raw underground techno when the night asks for it. From warm, sexy grooves to dark, hypnotic pressure, she builds each set around the room in front of her.</p>
  {chips(GENRES)}</div>
</div></section>

<section id="live" aria-label="Live photos"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Live</p><h2>Bangkok · Phuket · Thailand<span class="dot">.</span></h2></div></div>
  {GALLERY}
</div></section>

<section id="played"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Selected performances</p><h2>Where she's played<span class="dot">.</span></h2></div></div>
  {venues_html()}
  <p class="countries" style="margin-top:56px">Played in <span>{e(countries)}</span>.</p>
</div></section>

<section id="private"><div class="wrap split">
  <div><p class="label red">Private events</p><h2 class="h2">Weddings, hotels &amp; brand events<span class="dot">.</span></h2></div>
  <div class="prose"><p class="lead">Disco, house and feel-good grooves for weddings, hotel parties, rooftop events and brand launches in Bangkok, across Thailand and abroad.</p>
  <p><a class="btn" href="/wedding-dj-bangkok/">Weddings &amp; private events</a></p></div>
</div></section>

{book_cta()}

<section id="faq"><div class="wrap split">
  <div><p class="label red">FAQ</p><h2 class="h2">About DJ Berry<span class="dot">.</span></h2></div>
  <div>{faq_html(HOME_FAQ)}</div>
</div></section>
''', [faq_schema(HOME_FAQ)] + [event_schema(ev) for ev in UPCOMING], og_type="profile")

# ================= ABOUT =================
page("/about/", "About Berry Linn — Female DJ & Music Producer in Bangkok | DJ Berry",
     "The story of Berry Linn (DJ Berry): an early name in Myanmar's electronic music scene, now a Bangkok-based DJ and music producer playing house, afro house and techno worldwide.",
     "About", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <h1>Berry Linn<span class="dot">.</span></h1>
  <p class="lead">Female DJ &amp; music producer in Bangkok, known on the decks as DJ Berry.</p>
</div>
<section><div class="wrap split">
  <figure class="photo-wide"><img src="/images/berry-linn-music-producer-portrait.jpg" alt="Berry Linn lying on a white faux-fur coat, portrait for her 2026 press kit" width="1066" height="1600"></figure>
  <div class="prose">
    <p class="label red">In short</p>
    <p class="ai-bio">{e(S["short_bio"])}</p>
    <h2 class="h2" style="font-size:clamp(36px,5vw,64px);margin:40px 0 20px">From Myanmar to Bangkok<span class="dot">.</span></h2>
    <p>Berry was one of the <strong>early names in Myanmar's electronic music scene</strong>, active since 2018. From there she took her sound on the road, backpacking and playing across <strong>India, Sri Lanka, Singapore, Vietnam, the Philippines and Thailand</strong>, and completing an advanced DJ course in Goa along the way.</p>
    <p>Now rooted in Bangkok, her second home, she has played <strong>Wonderfruit, Sing Sing Theater, Mustache Bangkok, Baccarat, APT 101 and MU:IN</strong>, held residencies across the city, and is part of the <strong>Deep House Thailand</strong> lineup. Promoters book her for one thing above all: she reads a room fast and keeps the dancefloor moving.</p>
    <p>In March 2026 she released her first original track, <strong>“SACHI”</strong>, followed by <strong>“24 Turn It Up”</strong>. She is now taking bookings for clubs and festivals across Asia, Europe and beyond.</p>
    <blockquote class="pull">“{e(S["quote_life"])}”</blockquote>
    {stats}
  </div>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">The sound</p><blockquote class="pull">“{e(S["quote_sound"])}”</blockquote></div>
  <div>{chips(GENRES)}<p class="countries" style="margin-top:32px">Played in <span>{e(countries)}</span>.</p></div>
</div></section>
{book_cta()}
''', og_type="profile", image="/images/berry-linn-dj-producer-press-photo.jpg")

# ================= MUSIC =================
pl_cards = "".join(
    f'<article class="release"><span class="label">Playlist</span><h3 style="font-size:clamp(28px,3vw,40px)">{e(p["title"])}</h3><p>{e(p.get("description"))}</p>'
    + (f'<iframe class="embed" style="height:352px" title="{e(p["title"])} playlist on Spotify" src="https://open.spotify.com/embed/playlist/{spotify_id(p["url"], "playlist")}?utm_source=generator&amp;theme=0" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>' if spotify_id(p.get("url"), "playlist") else "")
    + "</article>" for p in PLAYLISTS)
page("/music/", "DJ Berry Music — Releases, Mixes & Spotify Playlists | Berry Linn",
     "Listen to DJ Berry (Berry Linn), Bangkok DJ and music producer: debut single SACHI (ft. BYAS), 24 Turn It Up, DJ mixes on SoundCloud and Berry's Spotify playlists.",
     "Music", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <h1>Music<span class="dot">.</span></h1>
  <p class="lead">Original productions, DJ mixes and playlists by Berry Linn. House, afro house and techno made in Bangkok.</p>
  <div class="row" style="margin-top:26px"><a class="btn red" href="{L["spotify"]}" target="_blank" rel="me noopener">Spotify</a><a class="btn" href="{L["soundcloud"]}" target="_blank" rel="me noopener">SoundCloud</a><a class="btn" href="{L["bandsintown"]}" target="_blank" rel="me noopener">Bandsintown</a></div>
</div>
<section><div class="wrap">
  <div class="sec-head"><div><p class="label red">As a producer</p><h2>Out now<span class="dot">.</span></h2></div></div>
  {release_cards()}
</div></section>
<section id="playlists"><div class="wrap">
  <div class="sec-head"><div><p class="label red">Curated by Berry</p><h2>Spotify playlists<span class="dot">.</span></h2></div><a class="btn small red" href="{L["spotify"]}" target="_blank" rel="noopener">Follow on Spotify</a></div>
  {f'<div class="releases">{pl_cards}</div>' if PLAYLISTS else f'<p class="lead" style="max-width:52ch">The tracks Berry is playing right now, from sunset grooves to late-night techno. <a href="{L["spotify"]}" target="_blank" rel="noopener" style="color:var(--red)">Open Berry’s playlists on Spotify →</a></p>'}
</div></section>
<section id="mixes"><div class="wrap">
  <div class="sec-head"><div><p class="label red">As a DJ</p><h2>DJ mixes<span class="dot">.</span></h2></div><a class="btn small red" href="{L["soundcloud"]}" target="_blank" rel="noopener">Follow on SoundCloud</a></div>
  {mix_cards()}
</div></section>
{book_cta()}
''')

# ================= EVENTS =================
page("/events/", "DJ Berry Events & Tour Dates | Bangkok, Thailand & Worldwide",
     "Upcoming gigs and tour dates for DJ Berry (Berry Linn), Bangkok DJ and music producer, plus her venue history across Thailand and Asia. Tickets and event details.",
     "Events", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <h1>Events<span class="dot">.</span></h1>
  <p class="lead">Where to catch DJ Berry next, in Bangkok and around the world.</p>
  <div class="row" style="margin-top:26px"><a class="btn red" href="{L["bandsintown"]}" target="_blank" rel="noopener">Follow on Bandsintown</a><a class="btn" href="{IG}" target="_blank" rel="noopener">Instagram</a></div>
</div>
<section><div class="wrap">
  <div class="sec-head"><div><p class="label red">Upcoming</p><h2>Tour dates<span class="dot">.</span></h2></div></div>
  {events_list(UPCOMING)}
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><p class="label red">Venue history</p><h2>Where she's played<span class="dot">.</span></h2></div></div>
  {venues_html()}
  <p class="countries" style="margin-top:56px">Played in <span>{e(countries)}</span>.</p>
</div></section>
<section aria-label="Live photos"><div class="wrap">{GALLERY}</div></section>
{book_cta()}
''', [event_schema(ev) for ev in UPCOMING])

# ================= BOOK =================
FORM = """<form id="booking-form" name="booking" method="POST" action="/thanks/" data-netlify="true" netlify-honeypot="company-website">
  <input type="hidden" name="form-name" value="booking">
  <p hidden><label>Leave empty <input id="hp" name="company-website"></label></p>
  <label>Your name<input id="f-name" name="name" required autocomplete="name"></label>
  <label>Email<input id="f-email" name="email" type="email" required autocomplete="email"></label>
  <label>Event date<input id="f-date" name="date" type="date"></label>
  <label>City / venue<input id="f-venue" name="venue" placeholder="e.g. Bangkok, rooftop bar"></label>
  <label class="full">Type of event
    <select id="f-type" name="event_type">
      <option>Club night</option><option>Festival</option><option>Hotel / rooftop / beach club</option><option>Tour / international booking</option>
      <option>Wedding</option><option>Private party</option><option>Corporate / brand event</option><option>Other</option>
    </select></label>
  <label class="full">Tell Berry about the event<textarea id="f-msg" name="message" placeholder="Set length, expected crowd, music style, fee and travel"></textarea></label>
  <div class="full"><button class="btn red" type="submit">Send booking request</button></div>
</form>"""
page("/book-dj/", "Book DJ Berry | Bangkok & International DJ Bookings",
     "Book DJ Berry, Bangkok-based female DJ and music producer, for clubs, festivals, hotels, rooftops, beach clubs, brand events and private events in Thailand, Asia, Europe and worldwide.",
     "Book DJ Berry", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <h1>Book Berry<span class="dot">.</span></h1>
  <p class="lead">Available for clubs, festivals, private events and tours across Asia, Europe and worldwide. Get in touch for dates, fees and travel.</p>
</div>
<section><div class="wrap split">
  <div class="contact"><dl>
    <div><dt>Email</dt><dd class="red"><a href="mailto:{EMAIL}">{EMAIL}</a></dd></div>
    <div><dt>WhatsApp</dt><dd><a href="{WA}" target="_blank" rel="noopener">{e(S["whatsapp"])}</a></dd></div>
    <div><dt>Instagram</dt><dd><a href="{IG}" target="_blank" rel="noopener">@berry_linn</a></dd></div>
    <div><dt>Based in</dt><dd>{e(S["based_in"])} · GMT+7</dd></div>
  </dl>
  <p class="label" style="margin-top:28px">Technical rider</p><p style="color:#DCD6CD">{e(S["tech_rider"])}</p></div>
  {FORM}
</div></section>
<section><div class="wrap split">
  <div><p class="label red">What Berry plays for</p><h2 class="h2">Clubs, festivals &amp; private events<span class="dot">.</span></h2></div>
  <div class="prose">{chips(["Nightclubs", "Festivals", "Rooftops", "Beach clubs", "Hotels", "Pool parties", "Brand events", "Weddings", "Private parties", "Tours"])}
  <p style="margin-top:24px">Played Wonderfruit, Full Moon Festival, Sing Sing Theater, Mustache Bangkok, Sofitel and venues across seven countries.</p></div>
</div></section>
''')

# ================= WEDDINGS =================
WED_FAQ = [
    ("Does DJ Berry play destination weddings in Thailand?", "Yes. Berry plays weddings in Bangkok and destination weddings across Thailand, including Phuket, Koh Samui and the islands."),
    ("What music does Berry play at weddings?", "Warm deep house and lounge for cocktails and dinner, then disco, 80s and 90s classics, nu-disco edits and house music for the party. Your must-play and do-not-play lists are always followed."),
    ("Does Berry play hotel, corporate and brand events?", "Yes. Hotel parties, rooftop events, brand launches, birthdays and villa parties in Bangkok and across Thailand."),
    ("How far ahead should we book?", "Weddings are best booked 3 to 6 months ahead, especially for weekends in the November to April high season."),
]
WED_CTA = book_cta('Book your wedding DJ<span class="dot">.</span>', "Tell Berry your date, venue and the kind of night you want. Bangkok, anywhere in Thailand, or abroad.")
page("/wedding-dj-bangkok/", "Wedding DJ Bangkok & Private Event DJ | DJ Berry",
     "DJ Berry is a female wedding and private event DJ in Bangkok for weddings, destination weddings in Thailand, hotel, rooftop and brand events. Disco, house and 80s–90s classics.",
     "Wedding DJ Bangkok", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <h1>Wedding DJ Bangkok<span class="dot">.</span></h1>
  <p class="lead">A female DJ for weddings, destination weddings in Thailand, hotel parties and brand events. Stylish music that suits your crowd, from the first drink to the last dance.</p>
  <div class="row" style="margin-top:26px"><a class="btn red" href="/book-dj/">Check my date</a></div>
</div>
<section><div class="wrap split">
  <div><p class="label red">The night</p><h2 class="h2">How the music flows<span class="dot">.</span></h2></div>
  <ul class="events" style="border-top-color:var(--line)">
    <li class="event"><time>1<small>Welcome</small></time><div><h3>Ceremony &amp; welcome drinks</h3><p>Soft lounge, acoustic edits and gentle deep house.</p></div></li>
    <li class="event"><time>2<small>Dinner</small></time><div><h3>Dinner</h3><p>Warm deep house and organic grooves that leave room for conversation.</p></div></li>
    <li class="event"><time>3<small>First dance</small></time><div><h3>Your song</h3><p>Your chosen track, mixed in cleanly.</p></div></li>
    <li class="event"><time>4<small>Party</small></time><div><h3>Dancefloor</h3><p>Disco, 80s and 90s classics, nu-disco edits and house music to fill the floor.</p></div></li>
  </ul>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">Private &amp; corporate</p><h2 class="h2">Private event DJ in Bangkok<span class="dot">.</span></h2></div>
  <div class="prose"><p class="lead">Hotel events, rooftop parties, brand launches, birthdays and villa parties. Experienced with hotel venues such as Sofitel and with festival crowds at Wonderfruit.</p>
  {chips(["Destination weddings", "Hotel events", "Rooftop parties", "Brand launches", "Villa parties", "Birthdays"])}</div>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">FAQ</p><h2 class="h2">Wedding questions<span class="dot">.</span></h2></div>
  <div>{faq_html(WED_FAQ)}</div>
</div></section>
{WED_CTA}
''', [faq_schema(WED_FAQ), {"@type": "Service", "name": "Wedding and private event DJ in Bangkok", "serviceType": "Wedding DJ",
      "provider": {"@id": f"{SITE}/#berrylinn"}, "areaServed": ["Bangkok", "Thailand"]}])

# ================= PRESS KIT =================
refs = "".join(f'<li><b>{e(r["name"])}</b><span>{e(r["role"])}</span></li>' for r in S["references"])
page("/press-kit/", "DJ Berry Press Kit (EPK) 2026 | Berry Linn, DJ & Producer",
     "Official 2026 electronic press kit for DJ Berry (Berry Linn), Bangkok-based DJ and music producer: bio, music, venue history, technical rider, press photos and booking contact.",
     "Press kit", f'''
<div class="wrap page-hero">{{{{CRUMBS}}}}
  <p class="label">DJ &amp; Producer · Electronic press kit · 2026</p>
  <h1>Press kit<span class="dot">.</span></h1>
  <p class="lead">For promoters, venues and press. Please use the biographies below as written.</p>
</div>
<section><div class="wrap split">
  <div><p class="label red">Short bio</p><h2 class="h2" style="font-size:clamp(36px,5vw,64px)">One paragraph<span class="dot">.</span></h2></div>
  <p class="ai-bio">{e(S["short_bio"])}</p>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">Long bio</p><h2 class="h2" style="font-size:clamp(36px,5vw,64px)">Slightly dangerous behind the decks<span class="dot">.</span></h2></div>
  <div class="prose">
    <p>Berry Linn, known on the decks as DJ Berry, is a Bangkok-based house and techno DJ with five years of professional performance behind her and a debut release out in 2026.</p>
    <p>Berry was one of the early names in Myanmar's electronic music scene, active since 2018. From there she took her sound on the road, backpacking and playing across India, Sri Lanka, Singapore, Vietnam, the Philippines and Thailand, and completing an advanced DJ course in Goa along the way.</p>
    <p>Now rooted in Bangkok, her second home, she has played Wonderfruit, Sing Sing Theater, Mustache Bangkok, Baccarat, APT 101 and MU:IN, held residencies across the city, and is part of the Deep House Thailand lineup. Promoters book her for one thing above all: she reads a room fast and keeps the dancefloor moving.</p>
    <p>In March 2026 she released her first original track, “SACHI”. She is now taking bookings for clubs and festivals across Asia, Europe and beyond.</p>
    {stats}
  </div>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">Booth</p><h2 class="h2" style="font-size:clamp(36px,5vw,64px)">Technical rider<span class="dot">.</span></h2></div>
  <div class="table-wrap"><table><tbody>
    <tr><th>Players</th><td>2 or 3 × Pioneer CDJ-3000 or CDJ-2000NXS2 (linked)</td></tr>
    <tr><th>Mixer</th><td>Pioneer DJM-900NXS2 or DJM-A9</td></tr>
    <tr><th>Monitors</th><td>Two booth monitors with separate volume control</td></tr>
    <tr><th>Media</th><td>USB (rekordbox)</td></tr>
  </tbody></table></div>
</div></section>
<section><div class="wrap split">
  <div><p class="label red">References</p><h2 class="h2" style="font-size:clamp(36px,5vw,64px)">Worked with<span class="dot">.</span></h2></div>
  <ul class="refs">{refs}</ul>
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><p class="label red">Press photos</p><h2>Photos<span class="dot">.</span></h2></div><p class="label">High-resolution files on request</p></div>
  <div class="gallery">
    {IMG("berry-linn-dj-producer-press-photo.jpg", "Berry Linn press photo in a black leather jacket", "g-b", w=1131, h=1600)}
    {IMG("berry-linn-female-dj-bangkok-portrait.jpg", "Berry Linn, female DJ in Bangkok, studio portrait with headphones", "g-c", w=1068, h=1600)}
    {IMG("dj-berry-black-and-white-portrait.jpg", "Black and white portrait of DJ Berry in sunglasses", "g-d", w=1066, h=1600)}
    {IMG("dj-berry-afro-house-producer-thailand.jpg", "DJ Berry, afro house producer in Thailand, outdoor portrait", "g-e", w=1280, h=1600)}
    {IMG("berry-linn-dj-producer-booking-portrait.jpg", "Berry Linn, DJ and producer, studio portrait", "g-b", w=1066, h=1600)}
    {IMG("dj-berry-berry-linn-portrait-bangkok.jpg", "Berry Linn seated beside a glass sign reading Berry", "g-c", w=1600, h=1600)}
  </div>
</div></section>
<section><div class="wrap">
  <div class="sec-head"><div><p class="label red">Venue history</p><h2>Where she's played<span class="dot">.</span></h2></div></div>
  {venues_html()}
</div></section>
{book_cta()}
''', image="/images/berry-linn-dj-producer-press-photo.jpg")

# ================= THANKS / 404 =================
page("/thanks/", "Thank you | DJ Berry", "Your booking request was sent.", "Thank you", """
<div class="wrap page-hero">{{CRUMBS}}<h1>Thank you<span class="dot">.</span></h1><p class="lead">Your booking request is on its way. Berry usually replies within 24 hours (Bangkok time).</p>
<div class="row" style="margin-top:26px"><a class="btn" href="/music/">Listen while you wait</a></div></div>""", noindex=True)
page("/404", "Page not found | DJ Berry", "This page does not exist.", "Not found", """
<div class="wrap page-hero"><h1>Wrong room<span class="dot">.</span></h1><p class="lead">The page you're looking for isn't here.</p>
<div class="row" style="margin-top:26px"><a class="btn red" href="/">Go home</a><a class="btn" href="/events/">See events</a></div></div>""", noindex=True)

# ================= STATIC FILES =================
shutil.copy("styles.css", OUT)
shutil.copytree("images", os.path.join(OUT, "images"), dirs_exist_ok=True)
open(f"{OUT}/site.js", "w").write("""// Hide events whose date has passed (in case the site hasn't been rebuilt yet).
(function(){var t=new Date();t.setHours(0,0,0,0);
document.querySelectorAll('.event[data-date]').forEach(function(li){var d=new Date(li.dataset.date+'T23:59:59');if(d<t)li.remove();});
document.querySelectorAll('.events').forEach(function(ul){if(!ul.children.length){var p=document.createElement('p');p.className='empty';p.textContent='New dates coming soon. Follow @berry_linn on Instagram.';ul.replaceWith(p);}});
// Booking form: sent by Netlify Forms on the live site; in a local preview, show a note instead.
var f=document.getElementById('booking-form');
if(f)f.addEventListener('submit',function(ev){if(/berrylinnmusic\\.com$|djberrymusic\\.com$|netlify\\.app$/.test(location.hostname))return;ev.preventDefault();var p=document.createElement('p');p.className='ok full';p.textContent='Preview only: messages are sent once the site is live.';f.replaceWith(p);});
})();
""")
open(f"{OUT}/favicon.svg", "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0D0C0C"/><text x="12" y="47" font-family="Arial Black,Arial" font-weight="900" font-size="40" fill="#F3EEE6">B</text><circle cx="48" cy="43" r="6" fill="#FF3B1F"/></svg>')
PAGES = ["/", "/about/", "/music/", "/events/", "/book-dj/", "/wedding-dj-bangkok/", "/press-kit/"]
open(f"{OUT}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in PAGES) + "</urlset>\n")
open(f"{OUT}/robots.txt", "w").write(f"""# Search engines and AI assistants are welcome
User-agent: *
Allow: /
Disallow: /thanks/

User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {SITE}/sitemap.xml
""")
up_txt = "\n".join(f"- {ev['date']}{(' ' + ev['time']) if ev.get('time') else ''}: {ev['name']} — {ev['venue']}, {ev.get('city')}" for ev in UPCOMING) or "- New dates announced on Instagram @berry_linn"
open(f"{OUT}/llms.txt", "w").write(f"""# DJ Berry (Berry Linn) — DJ & Music Producer

> {S["short_bio"]}

- Artist name: {S["artist_name"]}
- Stage name: {S["stage_name"]}
- Occupation: DJ and music producer
- Based in: {S["based_in"]} (available worldwide)
- From: {S["from"]}
- Genres: {", ".join(GENRES)}
- Releases: {"; ".join(f'{r["title"]} ({r.get("credit")}, {r.get("date")})' for r in RELEASES)}
- DJ mixes: {"; ".join(m["title"] + " — " + m["url"] for m in MIXES)}
- Lineup: Deep House Thailand
- Notable venues: Wonderfruit, Sing Sing Theater, Mustache Bangkok (resident), Baccarat, APT 101, MU:IN, Full Moon Festival, UOB Live, Shelter Phuket, Zouk Colombo
- Countries played: {countries}
- Bookings: {EMAIL} · WhatsApp {S["whatsapp"]} · {SITE}/book-dj/
- Profiles: {", ".join(SAME_AS)}

## Upcoming events
{up_txt}

## Pages
- [Home]({SITE}/)
- [About Berry Linn]({SITE}/about/)
- [Music, releases & playlists]({SITE}/music/)
- [Events & tour dates]({SITE}/events/)
- [Book DJ Berry]({SITE}/book-dj/)
- [Wedding & private event DJ Bangkok]({SITE}/wedding-dj-bangkok/)
- [Press kit]({SITE}/press-kit/)
""")
print("built", len(PAGES) + 2, "pages,", len(UPCOMING), "upcoming events")

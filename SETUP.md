# djberrymusic.com — go-live guide

The site is built from the small text files in `content/` (events, mixes, releases, playlists, bio).
You edit those in a simple editor (Pages CMS) and Netlify updates the site automatically.

## Step 1 — Put the files on GitHub (10 min)
1. Log in to github.com as **berrylinnbangkok-hub**.
2. Click **+** (top right) → **New repository** → name it `berrylinnmusic` → **Public** → **Create repository**.
3. On the next page click **uploading an existing file**.
4. Unzip `berrylinnmusic-website.zip` on your computer. Open the folder, select **everything inside it**
   (content, images, build.py, styles.css, netlify.toml, requirements.txt, .pages.yml, .gitignore)
   and drag it onto the GitHub page. Click **Commit changes**.
   - Mac: press Cmd + Shift + . in Finder to see the hidden `.pages.yml` and `.gitignore` files.

## Step 2 — Connect Netlify (5 min)
1. app.netlify.com → **Add new project → Import an existing project → GitHub**.
2. Choose `berrylinnmusic`. Netlify reads the settings automatically
   (build command `python3 build.py`, publish folder `site`). Click **Deploy**.
3. Wait 1–2 minutes. Open the `.netlify.app` link and check the site.
4. **Forms**: in Netlify → your project → **Forms** → enable form detection, then redeploy once.
   Turn on email notifications so booking requests reach berrylinnbangkok@gmail.com.

## Step 3 — Connect your domains (Namecheap)
1. Netlify → your project → **Domain management → Add a domain** → `djberrymusic.com`.
2. Also add `www.djberrymusic.com` (Netlify usually adds it for you).
3. In Namecheap → **Domain List → Manage → Advanced DNS** for each domain:
   - delete the old parking records
   - add the records Netlify shows you (usually an **A record** `@` → Netlify's IP, and a **CNAME** `www` → `yoursite.netlify.app`)
4. Wait up to 24 hours. Netlify adds HTTPS automatically.

## Step 4 — Your editor (Pages CMS)
1. Go to **app.pagescms.org** → **Sign in with GitHub** → allow access to `berrylinnmusic`.
2. You'll see: **Upcoming events, DJ mixes, My releases, Spotify playlists, Site settings & bio, Where I've played**.
3. Change something → **Save**. The live site updates in about 1 minute.
   - Events: date as `2026-11-14`, time as `22:00`. Past events disappear by themselves.
   - Playlists: Spotify → playlist → ⋯ → Share → Copy link to playlist → paste.

## Step 5 — Google & AI search
1. Google Search Console → add `djberrymusic.com` → verify (DNS TXT in Namecheap) → submit `https://djberrymusic.com/sitemap.xml`.
2. Bing Webmaster Tools → import from Google (helps ChatGPT / Copilot search).
3. Put **djberrymusic.com** in your Instagram, Spotify, SoundCloud, Bandsintown and Facebook bios.
4. Update the old Wix press kit: "Official site: djberrymusic.com".

## Still to add
- [ ] Spotify playlist links (Music page shows a "Follow on Spotify" button until then)
- [ ] Event posters for the Halloween parties
- [ ] Ticket link for Deep House Thailand Takeover at APT 101
- [ ] YouTube / TikTok / Resident Advisor links (if any)
- [ ] Bangkok Guide + newsletter (next phase)

# sansle

A quit tracker ("sansle" = without it). One person's private app, used mostly on an iPhone as an installed web app.

Live: https://cu-rt.github.io/sansle/ (GitHub Pages, built from `main`, repo root). Anything merged to `main` is live about a minute later. There is no build step.

## Files

- `index.html`: the whole app. HTML, CSS and JS inline, no framework, no dependencies except DM Sans from Google Fonts. Edit this file directly.
- `sw.js`: service worker. Pages come network-first, everything else cache-first.
- `manifest.webmanifest`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`: install metadata and icons.
- `tools/mock_server.py`: local test server with a fake account service (see Testing).

## Rules for every change

1. **Bump `CACHE` in `sw.js`** (`sansle-v3` → `sansle-v4` …) whenever `index.html` or any cached file changes, or installed copies keep serving the old files offline.
2. **Never let the service worker answer `*.supabase.co` requests.** Account data must always be live. The skip rule near the top of the fetch handler must stay.
3. **Never put a Supabase secret or service-role key in the repo.** The `sb_publishable_…` key in `index.html` is meant to be public; row-level security protects the data.
4. Check the inline script still parses: extract the `<script>` block and run `node --check` on it.
5. Keep it working at 375px wide with no sideways scroll, and respect `prefers-reduced-motion`.
6. Changes reach the phone when merged to `main`. If you work on a branch, open a PR and say so plainly. The owner merges it from the GitHub app.

## The owner's design preferences

- Calm and uncluttered. The owner repeatedly asked for "less busy". Don't add text lines, labels or explanations without being asked.
- Palette "Moonlight", Night layout: tokens on `:root`: `--field #0d1220`, `--white #dce4f5`, `--dim #a9b5cf`, `--chalk`/`--volt #c9d6f2`, DM Sans throughout.
- Four tabs: progress, milestones, tides, goals. Projects live in a sidebar revealed by dragging the page right.
- Progress tab: the largest non-zero unit big under the title, the running clock below with **two-digit** milliseconds, "Previous best" smaller on the right of the clock, a `streak | next milestone` switch at top left that changes **only when tapped**, never on its own.
- Before a visible redesign, show mockups and wait for a pick.

## Data and sync

All data is one JSON "store" in `localStorage` under `sanslr.v1` (the old spelling is deliberate, don't rename it): `{ v, updatedAt, active, projects: [...] }`. A project holds `id, name, hidden, start, runs[{start,end}], urges[{t, goal, status}], goals[{id,text}], milestones[{id,amount,unit,note}], won{start,ids,pb}`. `normalize()` upgrades old single-project saves.

Signed-in users also sync to Supabase (project `sansle`, ref `mhdliqisvgbqktrztmhf`, region eu-west-2, free plan):

- Table `public.user_state(user_id uuid pk → auth.users, data jsonb ≤ 2 MB, rev bigint, updated_at)`, row-level security on and forced, one policy per action allowing only `auth.uid() = user_id`, no access for `anon`.
- Function `public.save_state(p_data jsonb, p_rev bigint) returns bigint`, `security invoker`. It inserts, or updates only if the stored `rev` still equals `p_rev`, and returns the new `rev`. `null` means another device saved first.
- The client (search `/* ---------- Accounts`) talks to the REST and auth endpoints with plain `fetch`. Sync: pull the row; if its `rev` is newer, take it, or merge it with unsaved local edits (`mergeIn`, or `firstMerge` the first time a device meets an account); then push with the last seen `rev`, retrying on conflict. Local keys: `sansle.session` (tokens), `sansle.sync` (`owner, rev, joined, dirty`), `sansle.asked`.
- Merging: the newest store wins, but urges, goals and milestones from both sides are kept. On a device's first sync, the longer streak wins.
- Signing out removes local data. Signing in as a different person resets local data first, so nobody inherits someone else's data.
- Sign-in is email and password, with email confirmation. Supabase's free tier sends its own default confirmation email (custom templates need a custom email provider). The link lands on the site with a result in the address hash; the app reads it, removes it and asks for the password. It deliberately never signs in from the link.
- There is no password reset in the app yet.
- `window.claude` code paths are a leftover from when this was a Claude artifact. They are harmless outside Claude.

Database or auth settings changes happen in the Supabase dashboard, not in this repo. Writing to people's data rows is a last resort and needs the owner's say-so.

## Testing

```bash
python tools/mock_server.py      # http://localhost:8791
```

It serves this repo with the account service faked in memory, so you can sign up, sign in, sync, go offline and sign out without real accounts. Use any email; confirm it with `GET /__confirm?e=<email>`. Use `/__state` to see what was saved, and `/__offline?on` / `?off` to simulate losing connection. To fake a second device, save `localStorage`, clear it, reload and sign in again. Unregister the service worker between runs if you change `sw.js`.

What can't be tested here: the real confirmation email and an actual iPhone. Say so when reporting.

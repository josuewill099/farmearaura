# Fill these before publishing

## 1. Placeholders in the legal pages
Edit `locales/legal-es.json` and `locales/legal-pt.json`, then rebuild.

- `[TU NOMBRE O RAZÓN SOCIAL]` / `[SEU NOME OU RAZÃO SOCIAL]` — 2 occurrences each
  (privacy + about). Whoever is the data controller: you personally, or a company.
- `[PAÍS]` — 4 occurrences. Where the controller is established. This decides which
  supervisory authority applies.

## 2. Mailboxes
`hola@farmearaura.com` and `contato@farmearaura.com` are referenced across the
pages but do not exist yet. Create both (or point one at the other) — a contact
page with a dead address is worse than no contact page.

## 3. Verify the cookie claim yourself
The policies state the site sets no cookies. Confirm in DevTools → Application →
Cookies on the live domain after deploy. If Cloudflare Bot Fight Mode is on it may
set `__cf_bm`; the policy already allows for a strictly-necessary security cookie,
but check it matches reality.

## 4. Self-host the fonts
Both privacy policies currently disclose that Google Fonts receives the visitor's
IP, and promise this is being removed. Base64-inline or self-host the three fonts
and delete that bullet. This also fixes the share-card rendering problem in the
TikTok webview — same fix, two problems.

## 5. Not legal advice
These are plain-language templates that describe what the site actually does.
They are accurate as written, but they are not reviewed by a lawyer. If the site
starts collecting anything — analytics, ads, an email list — get them reviewed.

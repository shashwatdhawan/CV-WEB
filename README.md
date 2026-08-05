# Cloudverse Store

Run locally:

```bash
python -m uvicorn backend.main:app --reload
```

Edit products, prices, Discord invite, rank perks, and category labels in:

```text
static/store-config.js
```

Edit coupon codes in:

```text
static/coupons.json
```

Discord invite currently used by the site:

```text
https://discord.gg/8ZucR4fXkk
```

## DDoS Protection

Static website code cannot stop a real DDoS by itself. Put the site behind Cloudflare or another protected hosting/CDN layer.

Recommended setup:

1. Point your domain DNS through Cloudflare.
2. Enable Cloudflare proxy for the website record.
3. Turn on Bot Fight Mode or Super Bot Fight Mode if available.
4. Add WAF rate limits for repeated requests to `/login`, `/auth/callback`, and `/api/*`.
5. Keep the server IP private when possible.
6. Use HTTPS only.

This keeps the website online through Cloudflare's edge instead of exposing your origin directly.

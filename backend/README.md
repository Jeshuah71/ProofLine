# Deployment configuration

Set this environment variable on Enzonic:

```text
PROOFLINE_FRONTEND_ORIGIN=https://proofline.jeshuah024.workers.dev
```

Use an origin only (scheme and hostname, without a path). If unset or blank,
the backend defaults to this Cloudflare frontend. Surrounding whitespace and
trailing slashes are removed. An explicit value replaces the production default;
`http://localhost:5173` and `http://127.0.0.1:5173` remain allowed in either case.
The backend reads this setting at startup; restart/redeploy after changing it.
The example file is documentation and is not automatically loaded by `main.py`.

The frontend's `frontend/.env.production` sets:

```text
VITE_API_URL=https://proofline-1c2f81a3.enzonic.dev
```

If Cloudflare defines `VITE_API_URL` in its build environment, use the same URL
(without a trailing slash). Vite embeds this value during the build, so changing
it requires a rebuild. Local development continues to use `.env.development`.

CORS is registered outside the request body limiter, allowing preflights and
adding CORS headers to normal responses and handled errors, including 413,
422, 429, and 503. A proxy/startup failure or an unhandled server error can still
return a response without CORS headers; check backend status and deployment logs
when diagnosing those failures. Do not disable body limits or rate limits.

Run backend checks with:

```sh
cd backend
source .venv/bin/activate
python -m pytest -v
```

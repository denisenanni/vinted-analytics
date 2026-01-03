Deploy the Vinted Analytics application.

## API Deployment (Railway/Render)

1. Push to GitHub
2. Connect repo to Railway/Render
3. Set environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `USE_SUPABASE=true`
4. Set start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
5. Set root directory: `api`

## Web Deployment (Vercel/Netlify)

1. Push to GitHub
2. Connect repo to Vercel/Netlify
3. Set:
   - Build command: `npm run build`
   - Output directory: `dist`
   - Root directory: `web`
4. Set environment variable:
   - `VITE_API_URL=https://your-api-url.railway.app`

## Scraper (GitHub Actions)

Already configured in `.github/workflows/`. Just need secrets:
- `SUPABASE_URL`
- `SUPABASE_KEY`

Set in: GitHub repo → Settings → Secrets and variables → Actions

## Post-deploy checklist
- [ ] API /docs loads
- [ ] Web can fetch from API (check CORS)
- [ ] Scraper runs on schedule
- [ ] No Supabase connection errors in logs

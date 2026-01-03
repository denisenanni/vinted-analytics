Start the local development environment.

```bash
# Terminal 1: API
cd api
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 2: Web
cd web
npm run dev
```

Quick health check:
- API: http://localhost:8000/docs
- Web: http://localhost:5173

If API won't start:
1. Check .env has SUPABASE_URL and SUPABASE_KEY
2. Clear Python cache: `find . -name __pycache__ -exec rm -rf {} +`
3. Reinstall deps: `pip install -r requirements.txt`

If web won't start:
1. Check node_modules exists: `npm install`
2. Check VITE_API_URL in .env (or use default localhost:8000)

Debug a failing GitHub Actions workflow.

Error context: $ARGUMENTS

## Common Failures

### 1. Supabase timeout/500 error
```
postgrest.exceptions.APIError: {'message': 'canceling statement due to statement timeout'...}
```
**Fix**: Add pagination and retry logic to the failing query in `scraper/src/storage/database.py` or `scraper/src/jobs/cleanup.py`

### 2. Missing secrets
```
SUPABASE_URL or SUPABASE_KEY is not set
```
**Fix**: Add secrets in GitHub → Settings → Secrets → Actions

### 3. Rate limiting
```
HTTP 429 Too Many Requests
```
**Fix**: Add delays between requests in scraper, or reduce pages per run

### 4. Import errors
```
ModuleNotFoundError: No module named 'xxx'
```
**Fix**: Add missing package to `requirements.txt`

### 5. Scraper blocked
```
HTTP 403 Forbidden
```
**Fix**: Vinted may have blocked the IP. Usually transient with GitHub Actions rotating IPs.

## Debugging Steps

1. Check the full error in Actions → Click failed run → Click failed job
2. Look at which step failed
3. Check if it's a code issue or infrastructure issue
4. For transient errors: re-run the workflow
5. For code errors: fix locally, test with `/project:scrape`, then push

## Re-run Workflow
GitHub → Actions → Select workflow → Re-run failed jobs

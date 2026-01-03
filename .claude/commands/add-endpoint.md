Add a new API endpoint to the Vinted Analytics project.

The user will provide: $ARGUMENTS

Steps:
1. Add the business logic function in `api/src/services/analytics.py`
2. Add Pydantic response models in `api/src/models/schemas.py` (check for duplicates!)
3. Add the route in `api/src/routes/api.py` with proper typing
4. Add TypeScript interfaces in `web/src/api/client.ts`
5. Add the API function in `web/src/api/client.ts`

Remember:
- Use pagination for Supabase queries (page_size=1000, safety limit 50000)
- Add retry_supabase wrapper for queries that might timeout
- Convert Polish prices to EUR (divide by 4.3)
- Return sensible defaults when no data

After creating the endpoint, suggest the React component structure if needed.

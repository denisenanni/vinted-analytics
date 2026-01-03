Run the Vinted scraper manually for testing.

Arguments: $ARGUMENTS

Default command:
```bash
cd scraper
source ../api/venv/bin/activate  # or create scraper venv
pip install -r requirements.txt
python -m src.main --market IT --category women/dresses --pages 2
```

Available options:
- `--market`: IT, FR, DE, ES, NL, PL, BE, AT, PT
- `--category`: e.g., women/dresses, men/trainers, women/handbags
- `--pages`: Number of pages to scrape (each page ~96 items)
- `--cleanup`: Run daily cleanup job instead of scraping

Categories reference:
- Women: dresses, tops-and-t-shirts, jeans, trainers, handbags, sunglasses
- Men: tops-and-t-shirts, jeans, trainers, outerwear, watches

Environment required:
- SUPABASE_URL
- SUPABASE_KEY  
- USE_SUPABASE=true

Run the scraper with the user's specified parameters, or suggest appropriate defaults.

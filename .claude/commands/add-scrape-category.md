Add a new scraping category to GitHub Actions.

User wants to add: $ARGUMENTS

Steps:
1. Identify which workflow file to edit in `.github/workflows/`:
   - `scrape-it.yml` - Italy
   - `scrape-fr.yml` - France
   - etc.

2. Add the category to the matrix:
```yaml
strategy:
  matrix:
    include:
      - category: women/dresses
      - category: women/handbags
      - category: YOUR_NEW_CATEGORY  # Add here
```

3. Make sure the category path matches Vinted's URL structure:
   - Check on vinted.it/catalog?catalog[]=CATEGORY_ID
   - Common patterns: `women/dresses`, `men/trainers`, `women/handbags`

4. Consider adding to multiple markets if relevant

Available category paths:
- Women clothing: dresses, tops-and-t-shirts, jumpers-and-sweaters, jeans, outerwear
- Women shoes: boots, heels, trainers, sandals
- Women bags: handbags, backpacks, shoulder-bags, tote-bags
- Women accessories: jewellery, watches, sunglasses, belts
- Men clothing: tops-and-t-shirts, jeans, outerwear, suits-and-blazers
- Men shoes: trainers, boots, formal-shoes
- Men accessories: watches, sunglasses, bags-and-backpacks

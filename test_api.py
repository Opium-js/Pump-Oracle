from src.data.fetcher import get_new_solana_pairs

pairs = get_new_solana_pairs()

if pairs:
    import json
    print(f"\nPrzykładowa para:")
    print(json.dumps(pairs[0], indent=2))
else:
    print("Brak danych!")
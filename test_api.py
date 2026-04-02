from src.data.fetcher import get_new_solana_pairs
from src.analyzers.onchain import analyze_pairs, get_interesting_pairs

pairs = get_new_solana_pairs()
df = analyze_pairs(pairs)

if not df.empty:
    print(f"\nWszystkich par: {len(df)}")
    print(f"\nStatystyki danych:")
    print(f"  Płynność    - max: ${df['liquidity_usd'].max():,.0f}  | mediana: ${df['liquidity_usd'].median():,.0f}")
    print(f"  Wolumen 24h - max: ${df['volume_24h'].max():,.0f}  | mediana: ${df['volume_24h'].median():,.0f}")
    print(f"  Zmiana 1h   - max: {df['change_1h'].max():.1f}%  | mediana: {df['change_1h'].median():.1f}%")
    
    age_df = df[df['age_hours'].notna()]
    if not age_df.empty:
        print(f"  Wiek pary   - min: {age_df['age_hours'].min():.1f}h  | mediana: {age_df['age_hours'].median():.1f}h")

    print(f"\nTop 5 par wg wolumenu 24h:")
    top5 = df.nlargest(5, 'volume_24h')
    for _, r in top5.iterrows():
        age_str = f"{r['age_hours']:.0f}h" if r['age_hours'] else "?"
        print(f"  {r['name']:<20} vol: ${r['volume_24h']:>12,.0f} | liq: ${r['liquidity_usd']:>10,.0f} | 1h: {r['change_1h']:>6.1f}% | wiek: {age_str}")

    interesting = get_interesting_pairs(pairs)
    print(f"\nCiekawych tokenów: {len(interesting)}")

    for token in interesting:
        print(f"\n  {token['name']} ({token['dex'].upper()})")
        print(f"     Płynność:    ${token['liquidity_usd']:,.0f}")
        print(f"     Wolumen 24h: ${token['volume_24h']:,.0f}")
        print(f"     Zmiana 1h:   {token['change_1h']:.1f}%")
        print(f"     Wiek:        {token['age_hours']:.1f}h")
        print(f"     Buy/Sell:    {token['buy_sell_ratio']:.2f}")
        print(f"     Link:        {token['url']}")
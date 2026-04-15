"""Teste de qualidade de busca - verifica variedade e relevancia."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_fuzzy.settings')
import django
django.setup()

from recomendador.spotify_service import get_recommendations


def show_results(label, tracks):
    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")
    print(f"Total: {len(tracks)} musicas")

    artists_seen = set()
    for i, t in enumerate(tracks):
        name = t.get("name", "?")
        artist = t.get("artists", [{}])[0].get("name", "?")
        year = t.get("album", {}).get("release_date", "??")[:4]
        dup = " [DUPLICADO]" if artist in artists_seen else ""
        artists_seen.add(artist)
        print(f"  {i+1}. {name} - {artist} ({year}){dup}")

    unique_artists = len(artists_seen)
    print(f"\nArtistas unicos: {unique_artists}/{len(tracks)}")
    if unique_artists < len(tracks) * 0.5:
        print("  [!] Pouca variedade de artistas!")
    else:
        print("  [OK] Boa variedade!")


# Teste 1: Pop padrao
tracks = get_recommendations(0.5, 'pop', {'popularity': 50, 'nostalgia': 0.5})
show_results("POP PADRAO (score=0.5, pop=50, nosta=0.5)", tracks)

# Teste 2: Rock classico
tracks = get_recommendations(0.7, 'rock', {'popularity': 80, 'nostalgia': 0.9})
show_results("ROCK CLASSICO (score=0.7, pop=80, nosta=0.9)", tracks)

# Teste 3: Pop lancamentos
tracks = get_recommendations(0.8, 'pop', {'popularity': 90, 'nostalgia': 0.1})
show_results("POP LANCAMENTOS (score=0.8, pop=90, nosta=0.1)", tracks)

# Teste 4: Eletronica underground
tracks = get_recommendations(0.5, 'electronic', {'popularity': 10, 'nostalgia': 0.5})
show_results("ELETRONICA UNDERGROUND (score=0.5, pop=10, nosta=0.5)", tracks)

# Teste 5: Hip-hop energia alta
tracks = get_recommendations(0.9, 'hip-hop', {'popularity': 70, 'nostalgia': 0.5})
show_results("HIP-HOP ENERGIA (score=0.9, pop=70, nosta=0.5)", tracks)

print("\n" + "=" * 60)
print("TESTES FINALIZADOS")
print("=" * 60)

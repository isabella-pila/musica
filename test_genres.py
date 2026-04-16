import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_fuzzy.settings')
import django
django.setup()

from recomendador.spotify_service import get_recommendations

generos_para_testar = ['funk', 'sertanejo', 'rock', 'hip-hop', 'forro']

for g in generos_para_testar:
    print(f"\n{'#'*60}")
    print(f"### TESTANDO: {g.upper()}")
    print(f"{'#'*60}")
    tracks = get_recommendations(0.5, g, {'popularity': 50, 'nostalgia': 50})
    print(f"\n=== RESULTADO {g.upper()} ===")
    for i, t in enumerate(tracks):
        name = t["name"]
        artist = t["artists"][0]["name"]
        print(f"  {i+1}. {name} - {artist}")
    print(f"  Total: {len(tracks)} musicas")

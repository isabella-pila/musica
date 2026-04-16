import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_fuzzy.settings')
import django
django.setup()
from recomendador.spotify_service import get_sp

sp = get_sp()
queries = [
    "baile funk", "funk carioca", "sertanejo", "pagode", "forro", 
    "mpb", "samba", "axe", "pop", "rock", "hip hop", "electronic", 
    "electronic dance", "jazz", "classical", "blues", "reggaeton", 
    "rap brasileiro", "indie", "metal", "country"
]

for q in queries:
    res = sp.search(q=f'genre:"{q}"', type="track", limit=1)
    items = res.get("tracks", {}).get("items", [])
    if items:
        print(f"[{q}] Encontrado: {items[0]['name']}")
    else:
        # Tenta sem aspas
        res2 = sp.search(q=f'genre:{q}', type="track", limit=1)
        items2 = res2.get("tracks", {}).get("items", [])
        if items2:
            print(f"[{q}] (Sem aspas) Encontrado: {items2[0]['name']}")
        else:
            print(f"[{q}] NAO ENCONTRADO EM NENHUM FORMATO")

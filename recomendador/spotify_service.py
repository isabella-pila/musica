import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests
import random

# =========================
# AUTENTICAÇÃO
# =========================
auth_manager = SpotifyClientCredentials(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# =========================
# MAPEAMENTO DE GÊNEROS
# =========================
GENRE_SEED_MAP = {
    "funk":        "funk",
    "sertanejo":   "sertanejo",
    "pagode":      "pagode",
    "forro":       "forró",
    "forró":       "forró",
    "mpb":         "mpb",
    "samba":       "samba",
    "axe":         "axé",
    "axé":         "axé",
    "rock":        "rock",
    "pop":         "pop",
    "hip-hop":     "hip hop",
    "hip hop":     "hip hop",
    "rap":         "rap",
    "electronic":  "eletrônica",
    "eletronica":  "eletrônica",
    "eletrônica":  "eletrônica",
    "edm":         "edm",
    "jazz":        "jazz",
    "classical":   "clássica",
    "classica":    "clássica",
    "clássica":    "clássica",
    "blues":       "blues",
    "reggaeton":   "reggaeton",
    "r&b":         "r&b",
    "indie":       "indie",
    "metal":       "metal",
    "country":     "country",
}

def normalize_genre(genre):
    """Normaliza o gênero do formulário."""
    if not genre:
        return "pop"
    genre = genre.lower().strip()
    return GENRE_SEED_MAP.get(genre, genre)


# =========================
# QUERIES TEMÁTICAS POR MOOD + GÊNERO
# =========================
# Muitas queries variadas para compensar o limite de 10 tracks por busca.
# Cada query traz um ângulo diferente do mesmo sentimento.
MOOD_QUERIES = {
    # Score alto (≥0.7) — feliz, animado, festa
    'alto': {
        'funk':        ["funk pra festa", "funk animado", "funk pancadao",
                        "baile funk", "funk bass", "funk 2025",
                        "funk hit", "mc funk"],
        'sertanejo':   ["sertanejo animado", "sertanejo festa",
                        "sertanejo top", "esquenta sertanejo",
                        "sertanejo 2025 hit", "sertanejo piseiro",
                        "sertanejo ao vivo"],
        'pagode':      ["pagode animado", "pagode churras",
                        "roda pagode", "pagode 2025",
                        "pagode hit", "pagode ao vivo"],
        'forró':       ["forro animado", "forro pe de serra",
                        "forro hit", "sao joao forro",
                        "forro 2025", "piseiro"],
        'mpb':         ["mpb alegre", "mpb pra cima",
                        "mpb classico", "mpb animada"],
        'samba':       ["samba roda", "samba enredo",
                        "samba carnaval", "samba animado",
                        "pagode samba festa"],
        'axé':         ["axe carnaval", "axe hit",
                        "axe animado", "trio eletrico",
                        "axe bahia"],
        'pop':         ["pop hit 2025", "feel good pop",
                        "pop dance", "pop alegre",
                        "top pop", "pop brasil"],
        'rock':        ["rock energy", "rock hit",
                        "rock animado", "rock festa",
                        "rock nacional animado"],
        'hip hop':     ["hip hop hit", "rap hype",
                        "trap hit", "rap festa",
                        "rap brasileiro sucesso"],
        'eletrônica':  ["edm hit", "dance hit",
                        "electronic party", "festival edm",
                        "eletronica animada"],
        'jazz':        ["jazz swing", "upbeat jazz",
                        "jazz feel good", "jazz alegre"],
        'clássica':    ["classical uplifting", "classical energy",
                        "classical alegre"],
        'blues':       ["blues rock", "blues upbeat",
                        "blues groove", "blues animado"],
        'reggaeton':   ["reggaeton hit", "perreo",
                        "reggaeton party", "reggaeton 2025"],
        'rap':         ["rap brasileiro hit", "rap nacional",
                        "trap br", "rap sucesso"],
    },
    # Score médio (0.4–0.7) — chill, tranquilo, neutro
    'medio': {
        'funk':        ["funk melody", "funk romantico",
                        "funk suave", "funk love",
                        "funk lento"],
        'sertanejo':   ["sertanejo universitario", "sertanejo romantico",
                        "sertanejo 2025", "sertanejo top",
                        "sertanejo amor", "sertanejo acustico"],
        'pagode':      ["pagode romantico", "pagode suave",
                        "pagode relax", "pagode amor"],
        'forró':       ["forro romantico", "forro suave",
                        "forro xote", "forro amor"],
        'mpb':         ["mpb classica", "mpb essencial",
                        "bossa nova", "mpb tranquila",
                        "mpb acustico"],
        'samba':       ["samba jazz", "bossa nova chill",
                        "samba suave", "samba romantico"],
        'axé':         ["axe romantico", "axe suave"],
        'pop':         ["chill pop", "pop relax",
                        "indie pop", "pop acoustic",
                        "soft pop", "pop tranquilo"],
        'rock':        ["rock alternativo", "indie rock",
                        "soft rock", "rock acustico",
                        "rock romantico"],
        'hip hop':     ["lo-fi hip hop", "chill rap",
                        "hip hop relax", "rap chill",
                        "rap acustico"],
        'eletrônica':  ["chill electronic", "lo-fi beats",
                        "ambient music", "chillwave",
                        "eletronica calma"],
        'jazz':        ["smooth jazz", "jazz lounge",
                        "jazz relax", "jazz piano"],
        'clássica':    ["classical relax", "piano classico",
                        "classical study", "musica classica"],
        'blues':       ["slow blues", "blues acoustic",
                        "blues chill", "blues suave"],
        'reggaeton':   ["reggaeton lento", "reggaeton romantico"],
        'rap':         ["rap consciente", "rap nacional chill",
                        "rap acustico", "rap reflexao"],
    },
    # Score baixo (<0.4) — triste, melancólico, sofrência
    'baixo': {
        'funk':        ["funk triste", "funk melody triste",
                        "funk sofrencia", "funk sad"],
        'sertanejo':   ["sofrencia sertaneja", "sertanejo sofrencia",
                        "sertanejo triste", "modao sertanejo",
                        "sertanejo dor cotovelo", "sertanejo fossa",
                        "sertanejo sofrimento"],
        'pagode':      ["pagode triste", "pagode sofrencia",
                        "pagode saudade", "pagode dor"],
        'forró':       ["forro triste", "forro sofrencia",
                        "forro saudade", "forro dor"],
        'mpb':         ["mpb triste", "mpb melancolica",
                        "mpb saudade", "mpb acustica triste"],
        'samba':       ["samba fossa", "samba triste",
                        "samba saudade", "samba dor"],
        'axé':         ["axe triste", "axe saudade"],
        'pop':         ["sad pop", "sad songs",
                        "heartbreak", "broken heart",
                        "crying playlist", "musica triste",
                        "pop triste"],
        'rock':        ["sad rock",
                        "rock melancolico", "post rock sad"],
        'hip hop':     ["sad rap", "emo rap",
                        "rap triste", "sad trap",
                        "hip hop triste"],
        'eletrônica':  ["sad electronic", "dark electronic",
                        "melancholic beats", "eletronica triste"],
        'jazz':        ["jazz melancolico", "jazz triste",
                        "blue jazz", "jazz noir"],
        'clássica':    ["classical sad", "classical melancholic",
                        "sad piano", "musica classica triste"],
        'blues':       ["sad blues", "delta blues",
                        "blues triste", "blues melancolico"],
        'reggaeton':   ["reggaeton triste", "reggaeton sad"],
        'rap':         ["rap triste", "rap depressao",
                        "rap sad brasileiro", "rap sofrimento"],
    },
}

def get_mood_queries(score, genre_label):
    """Retorna queries temáticas baseadas no score e gênero."""
    if score >= 0.7:
        mood_level = 'alto'
    elif score >= 0.4:
        mood_level = 'medio'
    else:
        mood_level = 'baixo'

    # Tenta o gênero normalizado
    queries = MOOD_QUERIES.get(mood_level, {}).get(genre_label, [])

    # Fallback genérico
    if not queries:
        fallback = {
            'alto':  [f"{genre_label} happy", f"{genre_label} party",
                      f"{genre_label} energy", f"{genre_label} hits",
                      f"{genre_label} animado", f"{genre_label} festa"],
            'medio': [f"{genre_label} chill", f"{genre_label} relax",
                      f"{genre_label} vibes", f"{genre_label} acoustic",
                      f"{genre_label} romantico"],
            'baixo': [f"{genre_label} sad", f"{genre_label} triste",
                      f"{genre_label} emotional", f"{genre_label} sofrencia",
                      f"{genre_label} melancolico"],
        }
        queries = fallback[mood_level]

    return queries


# =========================
# CHAVE ÚNICA (ANTI DUPLICAÇÃO)
# =========================
def track_key(track):
    """Gera chave única para identificar duplicatas."""
    try:
        name = track.get("name", "").lower().strip()
        artist = track.get("artists", [{}])[0].get("name", "").lower().strip()
        return f"{name}|{artist}"
    except:
        return None


# =========================
# BUSCAR TRACKS POR QUERY
# =========================
def search_tracks(query, limit=10):
    """
    Busca tracks diretamente pela API de search.
    Limite máximo de 10 em development mode do Spotify.
    """
    try:
        results = sp.search(q=query, type="track", limit=min(limit, 10))
        tracks = results.get("tracks", {}).get("items", [])
        print(f"[SEARCH] '{query}' -> {len(tracks)} resultados")
        return tracks
    except Exception as e:
        print(f"[SEARCH] Erro ao buscar '{query}': {e}")
        return []


# =========================
# COLETA DE MÚSICAS COM MÚLTIPLAS QUERIES
# =========================
def collect_tracks(queries, tracks_per_query=10):
    """
    Para cada query, busca tracks e combina.
    Remove duplicatas pelo track_key.
    Com limite de 10 por query, usamos múltiplas queries
    para obter uma boa variedade.
    """
    all_tracks = []
    seen_keys = set()

    for query in queries:
        tracks = search_tracks(query, limit=tracks_per_query)
        for t in tracks:
            if not t:
                continue
            key = track_key(t)
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_tracks.append(t)

    return all_tracks


# =========================
# RECOMENDAÇÃO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    """
    Função principal de recomendação.
    Usa múltiplas queries temáticas por mood+gênero,
    busca tracks diretamente pela API de search,
    e retorna top 10 músicas únicas.
    """
    genre_label = normalize_genre(genre)
    score = max(0.0, min(float(score), 1.0))
    data = data or {}

    # Gera queries temáticas baseadas no score fuzzy
    queries = get_mood_queries(score, genre_label)

    print(f"\n{'='*50}")
    print(f"[RECOMENDACAO] Genero: {genre_label} | Score: {score:.2f}")
    print(f"[RECOMENDACAO] Queries ({len(queries)}): {queries}")
    print(f"{'='*50}")

    # Busca com todas as queries
    all_tracks = collect_tracks(queries, tracks_per_query=10)

    print(f"[TOTAL] {len(all_tracks)} musicas unicas encontradas")

    # Fallback: se nenhuma query retornou resultado, tenta query genérica
    if not all_tracks:
        print("[FALLBACK] Tentando query generica...")
        fallback_queries = [genre_label, f"{genre_label} musica", f"{genre_label} hit"]
        all_tracks = collect_tracks(fallback_queries, tracks_per_query=10)

    # Embaralha para variedade e pega top 10
    random.shuffle(all_tracks)
    result = all_tracks[:10]

    print(f"\n[RESULTADO] {len(result)} musicas recomendadas:")
    for i, t in enumerate(result, 1):
        artist = t.get('artists', [{}])[0].get('name', '?')
        print(f"  {i}. {t.get('name', '?')} - {artist}")

    return result


# =========================
# CRIAR PLAYLIST
# =========================
def create_playlist(token, track_uris, score, genre):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        requests.get("https://api.spotify.com/v1/me", headers=headers).raise_for_status()

        # Nomes temáticos por mood
        if score >= 0.7:
            mood_label = "Energia Total 🔥"
        elif score >= 0.4:
            mood_label = "Vibes Chill 🌊"
        else:
            mood_label = "Sentimentos 💜"

        playlist_resp = requests.post(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            json={
                "name": f"FuzzyMood — {genre.title()} | {mood_label}",
                "public": True,
                "description": f"Playlist gerada pelo sistema fuzzy (score: {round(score * 100)}%)"
            }
        )
        playlist_resp.raise_for_status()
        playlist = playlist_resp.json()

        if track_uris:
            requests.post(
                f"https://api.spotify.com/v1/playlists/{playlist['id']}/items",
                headers=headers,
                json={"uris": track_uris}
            ).raise_for_status()

        return playlist["external_urls"]["spotify"]

    except Exception as e:
        print(f"Erro ao criar playlist: {e}")
        return None
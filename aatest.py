import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests
import time
import sys

def safe_print(msg):
    """Print seguro para Windows - substitui caracteres que o console nao suporta."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))

# =========================
# AUTENTICACAO SPOTIFY
# =========================
_sp_user = None

def build_sp(access_token):
    global _sp_user
    _sp_user = spotipy.Spotify(auth=access_token)
    return _sp_user

_sp_client = None
def get_sp():
    global _sp_client
    if _sp_client is None:
        auth = SpotifyClientCredentials(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET
        )
        _sp_client = spotipy.Spotify(auth_manager=auth, retries=0)
    return _sp_client


# =========================
# LAST.FM CONFIG
# =========================
LASTFM_API_KEY = settings.LASTFM_API_KEY
LASTFM_BASE    = "https://ws.audioscrobbler.com/2.0/"

LASTFM_PAGE           = 1
MAX_TRACKS_PER_ARTIST = 2

# Spotify retorna pop=0 para versões remasterizadas/ao vivo mesmo sendo músicas famosas.
# Deixamos 0 para não filtrar nada — a qualidade vem das tags do Last.fm.
MIN_POPULARITY = 0


# =========================
# MAPEAMENTO GENERO
# =========================
GENRE_SEED_MAP = {
    "funk":      "funk",
    "sertanejo": "sertanejo",
    "mpb":       "mpb",
    "pop":       "pop",
    "rock":      "rock",
}

def normalize_genre(genre):
    if not genre:
        return "pop"
    return GENRE_SEED_MAP.get(genre.lower().strip(), genre.lower().strip())


def get_mood_level(score):
    """
    5 moods espelhando os 5 níveis fuzzy de saída:
      muito_baixo  -> score < 0.20
      baixo        -> score < 0.40
      medio        -> score < 0.60
      alto         -> score < 0.80
      muito_alto   -> score >= 0.80
    """
    if score >= 0.80:
        return 'muito_alto'
    elif score >= 0.60:
        return 'alto'
    elif score >= 0.40:
        return 'medio'
    elif score >= 0.20:
        return 'baixo'
    else:
        return 'muito_baixo'


# =========================
# ARTISTAS POR GENERO — 5 MOODS
# =========================
GENRE_ARTISTS = {
    'muito_alto': {
        'funk':      ["MC Kevin o Chris", "Pedro Sampaio", "Dennis DJ", "MC Kevinho", "Ludmilla"],
        'sertanejo': ["Gusttavo Lima", "Jorge & Mateus", "Henrique e Juliano", "Xand Aviao", "Wesley Safadao"],
        'mpb':       ["Ivete Sangalo", "Gilberto Gil", "Jorge Ben Jor", "Tim Maia", "Caetano Veloso"],
        'pop':       ["Bruno Mars", "Dua Lipa", "The Weeknd", "Harry Styles", "Ariana Grande"],
        'rock':      ["AC/DC", "Foo Fighters", "Red Hot Chili Peppers", "Imagine Dragons", "Queen"],
    },
    'alto': {
        'funk':      ["Anitta", "MC Livinho", "MC Don Juan", "Mc Cabelinho", "Mc Hariel"],
        'sertanejo': ["Luan Santana", "Maiara e Maraisa", "Simone Mendes", "Zeze Di Camargo & Luciano", "Leonardo"],
        'mpb':       ["Marisa Monte", "Djavan", "Gilberto Gil", "Caetano Veloso", "Gal Costa"],
        'pop':       ["Taylor Swift", "Ed Sheeran", "Billie Eilish", "Adele", "Lady Gaga"],
        'rock':      ["Arctic Monkeys", "The Beatles", "Pink Floyd", "Nirvana", "Led Zeppelin"],
    },
    'medio': {
        'funk':      ["Mc Cabelinho", "MC Livinho", "Mc Hariel", "Ludmilla", "Anitta"],
        'sertanejo': ["Luan Santana", "Maiara e Maraisa", "Leonardo", "Zeze Di Camargo & Luciano", "Simone Mendes"],
        'mpb':       ["Caetano Veloso", "Marisa Monte", "Djavan", "Chico Buarque", "Maria Bethania"],
        'pop':       ["The Weeknd", "Billie Eilish", "Taylor Swift", "Ed Sheeran", "Lana Del Rey"],
        'rock':      ["Radiohead", "Arctic Monkeys", "Pink Floyd", "The Beatles", "Coldplay"],
    },
    'baixo': {
        'funk':      ["MC Cabelinho", "Mc Hariel", "MC Livinho", "Mc Don Juan", "MC Ryan SP"],
        'sertanejo': ["Leonardo", "Zeze Di Camargo & Luciano", "Luan Santana", "Gusttavo Lima", "Maiara e Maraisa"],
        'mpb':       ["Chico Buarque", "Caetano Veloso", "Maria Bethania", "Elis Regina", "Marisa Monte"],
        'pop':       ["Adele", "Billie Eilish", "Lana Del Rey", "Lewis Capaldi", "James Arthur"],
        'rock':      ["Nirvana", "Radiohead", "Pearl Jam", "The Cure", "Pink Floyd"],
    },
    'muito_baixo': {
        'funk':      ["MC Cabelinho", "Mc Hariel", "Mc Don Juan", "MC Ryan SP"],
        'sertanejo': ["Leonardo", "Zeze Di Camargo & Luciano", "Luan Santana", "Maiara e Maraisa", "Henrique e Juliano"],
        'mpb':       ["Chico Buarque", "Maria Bethania", "Elis Regina", "Caetano Veloso", "Marisa Monte"],
        'pop':       ["Adele", "Lana Del Rey", "Lewis Capaldi", "Billie Eilish", "Sufjan Stevens"],
        'rock':      ["Nirvana", "Radiohead", "The Cure", "Pearl Jam", "Linkin Park"],
    },
}

# =========================
# ARTISTAS BLOQUEADOS POR GENERO
# =========================
GENRE_BLOCKED_ARTISTS = {
    'rock':      ["harry styles", "taylor swift", "dua lipa", "ariana grande", "billie eilish",
                  "ed sheeran", "bruno mars", "adele", "lady gaga", "the weeknd",
                  "katy perry", "selena gomez", "justin bieber", "miley cyrus", "olivia rodrigo"],
    'pop':       [],
    'funk':      [],
    'sertanejo': [],
    'mpb':       [],
}


# =========================
# QUERY SPOTIFY POR GENERO — 5 MOODS
# =========================
GENRE_SPOTIFY_QUERY = {
    'muito_alto': {
        'funk':      "baile funk energia",
        'sertanejo': "sertanejo universitario",
        'mpb':       "mpb",
        'pop':       "dance pop",
        'rock':      "hard rock",
    },
    'alto': {
        'funk':      "funk carioca",
        'sertanejo': "sertanejo",
        'mpb':       "mpb bossa nova",
        'pop':       "pop",
        'rock':      "rock",
    },
    'medio': {
        'funk':      "funk melody",
        'sertanejo': "sertanejo romantico",
        'mpb':       "mpb",
        'pop':       "indie pop",
        'rock':      "indie rock",
    },
    'baixo': {
        'funk':      "funk triste",
        'sertanejo': "sertanejo sofrencia",
        'mpb':       "mpb melancolia",
        'pop':       "sad pop heartbreak",
        'rock':      "sad rock",
    },
    'muito_baixo': {
        'funk':      "funk saudade",
        'sertanejo': "sertanejo sofrencia choro",
        'mpb':       "mpb saudade",
        'pop':       "melancholic sad songs",
        'rock':      "emo rock",
    },
}


# =========================
# TAGS LAST.FM POR MOOD + GENERO — 5 MOODS
# =========================
LASTFM_TAGS = {
    'muito_alto': {
        'funk':      ["baile funk", "funk carioca", "funk brasileiro"],
        'sertanejo': ["sertanejo universitario", "forro", "sertanejo"],
        'mpb':       ["mpb", "brazilian music", "bossa nova"],
        'pop':       ["dance pop", "feel good", "pop"],
        'rock':      ["hard rock", "classic rock", "rock"],
    },
    'alto': {
        'funk':      ["funk carioca", "funk melody", "funk"],
        'sertanejo': ["sertanejo", "sertanejo romantico"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["pop", "indie pop"],
        'rock':      ["rock", "alternative rock"],
    },
    'medio': {
        'funk':      ["funk melody", "funk"],
        'sertanejo': ["sertanejo romantico", "sertanejo"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["indie pop", "acoustic pop", "pop"],
        'rock':      ["indie rock", "rock"],
    },
    'baixo': {
        'funk':      ["funk sofrencia", "funk"],
        'sertanejo': ["sofrencia", "sertanejo"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["sad pop", "indie pop"],
        'rock':      ["sad rock", "emo"],
    },
    'muito_baixo': {
        'funk':      ["funk sofrencia"],
        'sertanejo': ["sofrencia", "sertanejo triste"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["sad songs", "melancholic", "heartbreak"],
        'rock':      ["emo", "post-punk"],
    },
}


# =========================
# VALIDACAO DE GENERO
# =========================
def track_matches_genre(spotify_track, genre_label):
    blocked = GENRE_BLOCKED_ARTISTS.get(genre_label, [])
    if not blocked:
        return True
    track_artists = [a['name'].lower() for a in spotify_track.get('artists', [])]
    for ta in track_artists:
        if ta in blocked:
            safe_print(f"  [BLOCK] '{spotify_track['name']}' de '{ta}' bloqueado para genero '{genre_label}'")
            return False
    return True


# =========================
# LAST.FM: TOP TRACKS POR TAG
# =========================
def lastfm_tag_toptracks(tag, limit=50, page=LASTFM_PAGE):
    try:
        resp = requests.get(LASTFM_BASE, params={
            "method":  "tag.gettoptracks",
            "tag":     tag,
            "api_key": LASTFM_API_KEY,
            "format":  "json",
            "limit":   limit,
            "page":    page,
        }, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        tracks = data.get("tracks", {}).get("track", [])
        print(f"[LASTFM] tag='{tag}' page={page} -> {len(tracks)} tracks")
        return [{"name": t["name"], "artist": t["artist"]["name"]} for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM] Erro tag='{tag}': {e}")
        return []


# =========================
# LAST.FM: TOP TRACKS DE UM ARTISTA
# =========================
def lastfm_artist_toptracks(artist_name, limit=10):
    try:
        resp = requests.get(LASTFM_BASE, params={
            "method":  "artist.gettoptracks",
            "artist":  artist_name,
            "api_key": LASTFM_API_KEY,
            "format":  "json",
            "limit":   limit,
        }, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        tracks = data.get("toptracks", {}).get("track", [])
        print(f"[LASTFM ARTIST] '{artist_name}' -> {len(tracks)} tracks")
        return [{
            "name":   t["name"],
            "artist": t["artist"]["name"] if isinstance(t.get("artist"), dict) else artist_name,
        } for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM ARTIST] Erro '{artist_name}': {e}")
        return []


# =========================
# LAST.FM: TOP ARTISTS POR TAG
# =========================
def lastfm_tag_topartists(tag, limit=10, page=LASTFM_PAGE):
    try:
        resp = requests.get(LASTFM_BASE, params={
            "method":  "tag.gettopartists",
            "tag":     tag,
            "api_key": LASTFM_API_KEY,
            "format":  "json",
            "limit":   limit,
            "page":    page,
        }, timeout=8)
        resp.raise_for_status()
        data    = resp.json()
        artists = data.get("topartists", {}).get("artist", [])
        print(f"[LASTFM ARTISTS] tag='{tag}' page={page} -> {len(artists)} artistas")
        return [a["name"] for a in artists if a.get("name")]
    except Exception as e:
        print(f"[LASTFM ARTISTS] Erro tag='{tag}': {e}")
        return []


# =========================
# LAST.FM: CHART TOP TRACKS
# =========================
def lastfm_chart_toptracks(limit=50):
    try:
        resp = requests.get(LASTFM_BASE, params={
            "method":  "chart.gettoptracks",
            "api_key": LASTFM_API_KEY,
            "format":  "json",
            "limit":   limit,
        }, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        tracks = data.get("tracks", {}).get("track", [])
        print(f"[LASTFM CHART] {len(tracks)} tracks globais")
        return [{"name": t["name"], "artist": t["artist"]["name"]} for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM CHART] Erro: {e}")
        return []


# =========================
# SPOTIFY: BUSCAR URI POR NOME+ARTISTA
# =========================
def spotify_search_track(name, artist):
    try:
        sp = get_sp()
        results = sp.search(q=f"track:{name} artist:{artist}", type="track", limit=1, market="BR")
        items   = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]
        results = sp.search(q=f"{name} {artist}", type="track", limit=1, market="BR")
        items   = results.get("tracks", {}).get("items", [])
        return items[0] if items else None
    except spotipy.SpotifyException as e:
        if e.http_status == 429:
            raise e
        print(f"[SPOTIFY] Erro '{name} - {artist}': {e}")
        return None
    except Exception as e:
        print(f"[SPOTIFY] Erro '{name} - {artist}': {e}")
        return None


# =========================
# SPOTIFY: BUSCAR TRACKS POR GENERO (FALLBACK)
# limit=10 para evitar erro 400 do Spotify
# =========================
def spotify_search_genre(genre_label, mood, limit=10):
    try:
        sp = get_sp()
        q = GENRE_SPOTIFY_QUERY.get(mood, {}).get(genre_label, genre_label)
        results = sp.search(q=q, type="track", limit=limit, market="BR")
        items = results.get("tracks", {}).get("items", [])
        print(f"[SPOTIFY GENRE] query='{q}' -> {len(items)} tracks")
        return items
    except Exception as e:
        print(f"[SPOTIFY GENRE] Erro: {e}")
        return []


# =========================
# RECOMENDACAO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    """
    5 moods espelhando os 5 níveis fuzzy.
    MIN_POPULARITY = 0 (Spotify retorna pop=0 para versões remasterizadas).

      CAMADA 1: Last.fm tag.gettoptracks
      CAMADA 2: Last.fm artist.gettoptracks (complemento)
      CAMADA 3: Spotify search (fallback final)
    """
    genre_label = normalize_genre(genre)
    score       = max(0.0, min(float(score), 1.0))
    mood        = get_mood_level(score)

    known_artists = GENRE_ARTISTS.get(mood, {}).get(genre_label, [])
    tags          = LASTFM_TAGS.get(mood, {}).get(genre_label, [genre_label])[:4]

    print(f"\n{'='*60}")
    print(f"[RECOMENDACAO] Genero: {genre_label} | Score: {score:.2f} | Mood: {mood}")
    print(f"[RECOMENDACAO] Tags Last.fm: {tags}")
    print(f"[RECOMENDACAO] Artistas base: {known_artists}")
    print(f"[RECOMENDACAO] Max por artista: {MAX_TRACKS_PER_ARTIST}")
    print(f"{'='*60}")

    seen_keys     = set()
    lastfm_tracks = []

    # ========================================
    # CAMADA 1: tags
    # ========================================
    print(f"\n--- CAMADA 1: tag.gettoptracks ---")
    for tag in tags:
        tracks = lastfm_tag_toptracks(tag, limit=20)
        for t in tracks:
            key = f"{t['name'].lower()}|{t['artist'].lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                lastfm_tracks.append(t)
    print(f"[CAMADA 1] {len(lastfm_tracks)} tracks das tags")

    # ========================================
    # CAMADA 2: artistas
    # ========================================
    print(f"\n--- CAMADA 2: artist.gettoptracks (complemento) ---")
    primary_tag = tags[0] if tags else genre_label
    artists_from_tag = lastfm_tag_topartists(primary_tag, limit=8)
    all_artists = []
    seen_a = set()
    for a in artists_from_tag + known_artists:
        if a.lower() not in seen_a:
            seen_a.add(a.lower())
            all_artists.append(a)
    for artist_name in all_artists[:6]:
        tracks = lastfm_artist_toptracks(artist_name, limit=4)
        for t in tracks:
            key = f"{t['name'].lower()}|{t['artist'].lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                lastfm_tracks.append(t)
    print(f"[CAMADA 2] Total acumulado: {len(lastfm_tracks)} tracks")

    # ========================================
    # BUSCA NO SPOTIFY + FILTROS
    # ========================================
    print(f"\n--- Buscando no Spotify ---")
    result       = []
    artist_count = {}
    candidates   = lastfm_tracks[:80]

    for t in candidates:
        if len(result) >= 10:
            break
        try:
            spotify_track = spotify_search_track(t["name"], t["artist"])
            if not spotify_track:
                safe_print(f"  [X] Nao encontrado: {t['name']} - {t['artist']}")
                continue

            if not track_matches_genre(spotify_track, genre_label):
                continue

            artist_key = spotify_track['artists'][0]['name'].lower()
            if artist_count.get(artist_key, 0) >= MAX_TRACKS_PER_ARTIST:
                safe_print(f"  [SKIP] Limite por artista: {spotify_track['artists'][0]['name']}")
                continue

            artist_count[artist_key] = artist_count.get(artist_key, 0) + 1
            result.append(spotify_track)
            pop     = spotify_track.get('popularity', 0)
            release = spotify_track.get("album", {}).get("release_date", "?")
            safe_print(f"  [OK] {spotify_track['name']} - {spotify_track['artists'][0]['name']} (pop={pop}, {release})")

        except spotipy.SpotifyException as e:
            if getattr(e, 'http_status', None) == 429:
                print("[WAIT] Rate Limit do Spotify atingido.")
                break
        time.sleep(0.1)

    # ========================================
    # CAMADA 3: Spotify search (limit=10 fixo)
    # ========================================
    if len(result) < 10:
        print(f"\n--- CAMADA 3: Spotify search (faltam {10 - len(result)} tracks) ---")
        existing_uris = {r.get('uri') for r in result}

        for st in spotify_search_genre(genre_label, mood, limit=10):
            if len(result) >= 10:
                break
            if st.get('uri') in existing_uris:
                continue
            if not track_matches_genre(st, genre_label):
                continue
            artist_key = st['artists'][0]['name'].lower()
            if artist_count.get(artist_key, 0) >= MAX_TRACKS_PER_ARTIST:
                continue
            artist_count[artist_key] = artist_count.get(artist_key, 0) + 1
            result.append(st)
            existing_uris.add(st.get('uri'))
            safe_print(f"  [OK] (genero) {st['name']} - {st['artists'][0]['name']}")

    print(f"\n[RESULTADO FINAL] {len(result)} musicas | genero='{genre_label}' mood='{mood}'")
    return result


# =========================
# CRIAR PLAYLIST
# =========================
def create_playlist(token, track_uris, score, genre):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    try:
        requests.get("https://api.spotify.com/v1/me", headers=headers).raise_for_status()

        mood_label = "Energia Total" if score >= 0.7 else "Vibes Chill" if score >= 0.4 else "Sentimentos"

        playlist_resp = requests.post(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            json={
                "name":        f"HarmonAI - {genre.title()} | {mood_label}",
                "public":      True,
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
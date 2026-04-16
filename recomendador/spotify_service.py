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

# Sempre busca a página 1 do Last.fm = as mais escutadas/populares do gênero
LASTFM_PAGE = 1


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
    if score >= 0.7:
        return 'alto'
    elif score >= 0.4:
        return 'medio'
    return 'baixo'


# =========================
# ARTISTAS CONHECIDOS POR GENERO — MOOD NORMAL/ALTO
# =========================
GENRE_ARTISTS = {
    'funk':      ["MC Kevin o Chris", "Anitta", "Pedro Sampaio", "MC Livinho", "Ludmilla", "MC Don Juan", "Dennis DJ", "MC Kevinho", "Mc Cabelinho", "Mc Hariel"],
    'sertanejo': ["Gusttavo Lima", "Jorge & Mateus", "Henrique e Juliano", "Maiara e Maraisa", "Luan Santana", "Leonardo", "Simone Mendes", "Zeze Di Camargo & Luciano"],
    'mpb':       ["Caetano Veloso", "Gilberto Gil", "Djavan", "Maria Bethania", "Marisa Monte", "Chico Buarque", "Tim Maia", "Elis Regina", "Jorge Ben Jor", "Gal Costa"],
    'pop':       ["Taylor Swift", "The Weeknd", "Dua Lipa", "Harry Styles", "Billie Eilish", "Ed Sheeran", "Ariana Grande", "Bruno Mars", "Adele", "Lady Gaga"],
    'rock':      ["Foo Fighters", "Arctic Monkeys", "Red Hot Chili Peppers", "Nirvana", "Queen", "The Beatles", "Pink Floyd", "AC/DC", "Led Zeppelin", "Imagine Dragons"],
}

# =========================
# ARTISTAS CONHECIDOS POR GENERO — MOOD BAIXO (TRISTE)
# =========================
GENRE_ARTISTS_SAD = {
    'funk':      ["MC Cabelinho", "Mc Hariel", "MC Livinho"],
    'sertanejo': ["Leonardo", "Zeze Di Camargo & Luciano", "Luan Santana", "Gusttavo Lima", "Maiara e Maraisa"],
    'mpb':       ["Chico Buarque", "Caetano Veloso", "Maria Bethania", "Elis Regina", "Marisa Monte"],
    'pop':       ["Adele", "Billie Eilish", "Lewis Capaldi", "Lana Del Rey", "The Weeknd", "James Arthur"],
    'rock':      ["Nirvana", "Radiohead", "Pearl Jam", "The Cure", "Coldplay", "Pink Floyd"],
}

# =========================
# ARTISTAS PROIBIDOS POR GENERO
# Artistas que o Last.fm frequentemente associa a tags de outros gêneros
# e que nunca devem aparecer em determinado gênero
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
# QUERY SPOTIFY POR GENERO — MOOD NORMAL/ALTO
# =========================
GENRE_SPOTIFY_QUERY = {
    'funk':      "funk",
    'sertanejo': "sertanejo",
    'mpb':       "mpb",
    'pop':       "pop",
    'rock':      "rock",
}

# =========================
# QUERY SPOTIFY POR GENERO — MOOD BAIXO (TRISTE)
# =========================
GENRE_SPOTIFY_QUERY_SAD = {
    'funk':      "funk triste",
    'sertanejo': "sertanejo sofrencia triste",
    'mpb':       "mpb melancolia",
    'pop':       "sad pop heartbreak",
    'rock':      "sad rock",
}


# =========================
# TAGS LAST.FM POR MOOD + GENERO
# =========================
LASTFM_TAGS = {
    'alto': {
        'funk':      ["baile funk", "funk carioca", "funk brasileiro"],
        'sertanejo': ["sertanejo", "sertanejo universitario", "forro"],
        'mpb':       ["mpb", "bossa nova", "brazilian music"],
        'pop':       ["pop", "dance pop", "feel good"],
        'rock':      ["rock", "classic rock", "alternative rock"],
    },
    'medio': {
        'funk':      ["funk melody", "funk"],
        'sertanejo': ["sertanejo romantico", "sertanejo"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["pop", "indie pop", "acoustic pop"],
        'rock':      ["rock", "indie rock"],
    },
    'baixo': {
        'funk':      ["funk sofrencia"],
        'sertanejo': ["sofrencia", "sertanejo"],
        'mpb':       ["mpb", "bossa nova"],
        'pop':       ["sad pop", "indie pop", "pop"],
        'rock':      ["sad rock", "emo", "rock"],
    },
}


# =========================
# VALIDACAO DE GENERO
# Bloqueia artistas que não pertencem ao gênero solicitado
# =========================
def track_matches_genre(spotify_track, genre_label):
    """
    Retorna False se algum artista da track estiver na lista de bloqueados do gênero.
    Retorna True caso contrário (deixa passar).
    """
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
    """Busca as top tracks de uma tag no Last.fm."""
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
        return [{
            "name": t["name"],
            "artist": t["artist"]["name"],
        } for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM] Erro tag='{tag}': {e}")
        return []


# =========================
# LAST.FM: TOP TRACKS DE UM ARTISTA
# =========================
def lastfm_artist_toptracks(artist_name, limit=10):
    """Busca as top tracks de um artista especifico no Last.fm."""
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
            "name": t["name"],
            "artist": t["artist"]["name"] if isinstance(t.get("artist"), dict) else artist_name,
        } for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM ARTIST] Erro '{artist_name}': {e}")
        return []


# =========================
# LAST.FM: TOP ARTISTS POR TAG
# =========================
def lastfm_tag_topartists(tag, limit=10, page=LASTFM_PAGE):
    """Busca os top artistas de uma tag no Last.fm."""
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
    """Busca as musicas mais populares globalmente no Last.fm."""
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
        return [{
            "name": t["name"],
            "artist": t["artist"]["name"],
        } for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM CHART] Erro: {e}")
        return []


# =========================
# SPOTIFY: BUSCAR URI POR NOME+ARTISTA
# =========================
def spotify_search_track(name, artist):
    """Busca uma track no Spotify pelo nome+artista vindos do Last.fm."""
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
# =========================
def spotify_search_genre(genre_label, mood, limit=10):
    """Busca tracks diretamente no Spotify pelo genero+mood."""
    try:
        sp = get_sp()
        genre_query = GENRE_SPOTIFY_QUERY.get(genre_label, genre_label)
        if mood == 'baixo':
            sad_query = GENRE_SPOTIFY_QUERY_SAD.get(genre_label, genre_label)
            q = f'genre:"{genre_query}" {sad_query}'
        else:
            q = f'genre:"{genre_query}"'
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
    Fluxo com 3 camadas para garantir musicas do genero correto.
    Sempre retorna as mais populares/escutadas (LASTFM_PAGE = 1).
    Aplica filtro de artistas bloqueados para evitar vazamento de gênero.

      CAMADA 1: Last.fm tag.gettoptracks (tags de mood+genero)
      CAMADA 2: Last.fm artist.gettoptracks (artistas do genero filtrados por mood)
      CAMADA 3: Spotify search por genero+mood (fallback final)
    """
    genre_label = normalize_genre(genre)
    score       = max(0.0, min(float(score), 1.0))
    mood        = get_mood_level(score)

    known_artists = GENRE_ARTISTS_SAD.get(genre_label, []) if mood == 'baixo' else GENRE_ARTISTS.get(genre_label, [])
    tags = LASTFM_TAGS.get(mood, {}).get(genre_label, [genre_label])[:4]

    print(f"\n{'='*60}")
    print(f"[RECOMENDACAO] Genero: {genre_label} | Score: {score:.2f} | Mood: {mood}")
    print(f"[RECOMENDACAO] Popularidade: maxima (page={LASTFM_PAGE})")
    print(f"[RECOMENDACAO] Tags Last.fm: {tags}")
    print(f"[RECOMENDACAO] Artistas base: {known_artists}")
    print(f"{'='*60}")

    seen_keys     = set()
    lastfm_tracks = []

    # ========================================
    # Para mood baixo: Camada 2 PRIMEIRO
    # ========================================
    if mood == 'baixo':
        print(f"\n--- CAMADA 2 (prioritaria para mood baixo): artist.gettoptracks ---")
        for artist_name in known_artists[:6]:
            tracks = lastfm_artist_toptracks(artist_name, limit=5)
            for t in tracks:
                key = f"{t['name'].lower()}|{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    lastfm_tracks.append(t)
        print(f"[CAMADA 2] {len(lastfm_tracks)} tracks dos artistas sad do genero")

        print(f"\n--- CAMADA 1: tag.gettoptracks (complemento) ---")
        for tag in tags:
            tracks = lastfm_tag_toptracks(tag, limit=10)
            for t in tracks:
                key = f"{t['name'].lower()}|{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    lastfm_tracks.append(t)
        print(f"[CAMADA 1] Total acumulado: {len(lastfm_tracks)} tracks")

    else:
        # ========================================
        # Para alto/medio: Camada 1 primeiro, depois Camada 2
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

        print(f"\n--- CAMADA 2: artist.gettoptracks ---")
        primary_tag = tags[0] if tags else genre_label
        genre_artists_from_lastfm = lastfm_tag_topartists(primary_tag, limit=8)
        all_genre_artists = []
        seen_artists = set()
        for a in genre_artists_from_lastfm + known_artists:
            a_lower = a.lower()
            if a_lower not in seen_artists:
                seen_artists.add(a_lower)
                all_genre_artists.append(a)
        for artist_name in all_genre_artists[:6]:
            tracks = lastfm_artist_toptracks(artist_name, limit=5)
            for t in tracks:
                key = f"{t['name'].lower()}|{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    lastfm_tracks.append(t)
        print(f"[CAMADA 2] Total acumulado: {len(lastfm_tracks)} tracks")

    # ========================================
    # BUSCA NO SPOTIFY + FILTRO DE GENERO
    # ========================================
    print(f"\n--- Buscando no Spotify ---")
    result     = []
    candidates = lastfm_tracks[:60]  # um pouco mais para compensar os bloqueados

    for t in candidates:
        if len(result) >= 10:
            break
        try:
            spotify_track = spotify_search_track(t["name"], t["artist"])
            if spotify_track:
                # Filtra artistas que não pertencem ao gênero
                if not track_matches_genre(spotify_track, genre_label):
                    continue
                result.append(spotify_track)
                release = spotify_track.get("album", {}).get("release_date", "?")
                artist_name = spotify_track['artists'][0]['name']
                safe_print(f"  [OK] {spotify_track['name']} - {artist_name} ({release})")
            else:
                safe_print(f"  [X] Nao encontrado: {t['name']} - {t['artist']}")
        except spotipy.SpotifyException as e:
            if getattr(e, 'http_status', None) == 429:
                print("[WAIT] Rate Limit do Spotify atingido.")
                break
        time.sleep(0.1)

    # ========================================
    # CAMADA 3: Spotify search por genero+mood
    # ========================================
    if len(result) < 10:
        print(f"\n--- CAMADA 3: Spotify search por genero+mood (faltam {10 - len(result)} tracks) ---")
        existing_uris = {r.get('uri') for r in result}

        spotify_genre_tracks = spotify_search_genre(genre_label, mood, limit=15)
        for st in spotify_genre_tracks:
            if len(result) >= 10:
                break
            if st.get('uri') not in existing_uris:
                if not track_matches_genre(st, genre_label):
                    continue
                result.append(st)
                existing_uris.add(st.get('uri'))
                safe_print(f"  [OK] (genero) {st['name']} - {st['artists'][0]['name']}")

    print(f"\n[RESULTADO FINAL] {len(result)} musicas do genero '{genre_label}' mood '{mood}'")
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
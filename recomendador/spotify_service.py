import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests
import time

try:
    from ytmusicapi import YTMusic
    _ytm = YTMusic()
    YTM_AVAILABLE = True
except ImportError:
    _ytm = None
    YTM_AVAILABLE = False
    print("[YTMUSIC] ytmusicapi nao instalado.")


def safe_print(msg):
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

_sp_client     = None
_sp_token_info = None  # cache do token para uso direto via requests

def get_sp():
    """Retorna instância spotipy com retries TOTALMENTE desabilitados."""
    global _sp_client
    if _sp_client is None:
        auth = SpotifyClientCredentials(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET
        )
        # retries=0 e requests_timeout curto para não travar o servidor
        _sp_client = spotipy.Spotify(
            auth_manager=auth,
            retries=0,
            requests_timeout=8,
        )
    return _sp_client


def get_access_token():
    """Retorna token de acesso raw para chamadas diretas via requests."""
    sp    = get_sp()
    token = sp.auth_manager.get_access_token(as_dict=False)
    return token
 
 
# =========================
# MAPEAMENTO GENERO / MOOD
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
# QUERIES DO YTMUSIC POR GENERO + MOOD
# =========================
YTM_PLAYLIST_QUERIES = {
    'muito_alto': {
        'funk':      'baile funk pancadao 2024',
        'sertanejo': 'sertanejo universitario animado 2024',
        'mpb':       'mpb animada brasil',
        'pop':       'pop animado',
        'rock':      'rock energia hard rock',
    },
    'alto': {
        'funk':      'funk carioca hits',
        'sertanejo': 'sertanejo hits top',
        'mpb':       'mpb brasileira',
        'pop':       'pop hits internacional',
        'rock':      'rock classico hits',
    },
    'medio': {
        'funk':      'funk melody romantico',
        'sertanejo': 'sertanejo romantico',
        'mpb':       'mpb romantica',
        'pop':       'pop love songs 2025',
        'rock':      'rock alternativo indie',
    },
    'baixo': {
        'funk':      'funk triste saudade',
        'sertanejo': 'sertanejo sofrencia triste',
        'mpb':       'mpb triste saudade',
        'pop':       'pop best heartbreak ',
        'rock':      'rock triste sad rock',
    },
    'muito_baixo': {
        'funk':      'funk triste melancolico',
        'sertanejo': 'sertanejo sofrencia choro',
        'mpb':       'mpb saudade melancolia',
        'pop':       'sad pop songs',
        'rock':      'rock emo depressivo',
    },
}


# =========================
# YTMUSIC: BUSCAR PLAYLIST E RETORNAR TRACKS
# =========================
def ytm_get_playlist_tracks(genre_label, mood, top_n=15):
    """
    Busca playlist temática no YTMusic e retorna as top_n
    primeiras tracks com título e artista.
    """
    if not YTM_AVAILABLE:
        print("[YTM] ytmusicapi não disponível.")
        return []

    query = YTM_PLAYLIST_QUERIES.get(mood, {}).get(genre_label)
    if not query:
        print(f"[YTM] Nenhuma query para {genre_label}/{mood}")
        return []

    print(f"[YTM] Buscando playlist: '{query}'")

    try:
        search_results = _ytm.search(query, filter="playlists", limit=5)
    except Exception as e:
        print(f"[YTM] Erro na busca: {e}")
        return []

    for playlist_item in search_results:
        playlist_id    = playlist_item.get('browseId') or playlist_item.get('playlistId')
        playlist_title = playlist_item.get('title', '?')
        if not playlist_id:
            continue
        try:
            print(f"[YTM] Abrindo: '{playlist_title}'")
            playlist_data = _ytm.get_playlist(playlist_id, limit=top_n)
            tracks        = playlist_data.get('tracks', [])

            result = []
            for t in tracks[:top_n]:
                title   = (t.get('title') or '').strip()
                artists = t.get('artists') or []
                artist  = artists[0].get('name', '').strip() if artists else ''
                if title and artist:
                    result.append({'title': title, 'artist': artist})

            if result:
                print(f"[YTM] {len(result)} tracks extraídas de '{playlist_title}'")
                return result

        except Exception as e:
            print(f"[YTM] Erro ao abrir '{playlist_title}': {e}")

        time.sleep(0.2)

    print("[YTM] Nenhuma playlist retornou tracks.")
    return []


# =========================
# SPOTIFY: CROSS-SEARCH DIRETO VIA REQUESTS
# =========================
def spotify_find_track(title, artist):
    """
    Busca a track no Spotify pelo título+artista usando requests direto.
    Nunca lança exceção — retorna None em qualquer erro incluindo 429.

    1ª tentativa: track:"titulo" artist:"artista"  (precisa)
    2ª tentativa: "titulo artista"                 (ampla)
    """
    try:
        token   = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        base    = "https://api.spotify.com/v1/search"

        queries = [
            f'track:"{title}" artist:"{artist}"',
            f"{title} {artist}",
        ]

        for q in queries:
            try:
                resp = requests.get(
                    base,
                    headers=headers,
                    params={"q": q, "type": "track", "limit": 1, "market": "BR"},
                    timeout=6,
                )

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    print(f"  [429] Rate limit. Aguardando {retry_after}s...")
                    time.sleep(min(retry_after, 10))  # espera no máximo 10s
                    return None  # para não travar o servidor aguardando 80k s

                if resp.status_code != 200:
                    print(f"  [ERRO {resp.status_code}] '{title}'")
                    return None

                items = resp.json().get("tracks", {}).get("items", [])
                if items:
                    t = items[0]
                    safe_print(f"  [OK] {t['name']} - {t['artists'][0]['name']}")
                    return t

            except requests.exceptions.Timeout:
                print(f"  [TIMEOUT] '{title}'")
                return None
            except Exception as e:
                print(f"  [ERRO] '{title}': {e}")
                return None

        print(f"  [NÃO ACHOU] '{title}' - '{artist}'")
        return None

    except Exception as e:
        print(f"  [ERRO TOKEN] {e}")
        return None


# =========================
# RECOMENDACAO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    """
    1. Busca playlist temática no YTMusic (ex: "rock triste")
    2. Pega as 15 primeiras tracks da playlist
    3. Para cada track: cross-search no Spotify por título+artista
       — se 429, para imediatamente e retorna o que já achou
    4. Retorna até 10 tracks encontradas
    """
    genre_label = normalize_genre(genre)
    score       = max(0.0, min(float(score), 1.0))
    mood        = get_mood_level(score)

    print(f"\n{'='*60}")
    print(f"[RECOMENDACAO] Genero: {genre_label} | Score: {score:.2f} | Mood: {mood}")
    print(f"{'='*60}")

    if not YTM_AVAILABLE:
        print("[RECOMENDACAO] YTMusic não disponível.")
        return []

    ytm_tracks = ytm_get_playlist_tracks(genre_label, mood, top_n=15)

    if not ytm_tracks:
        print("[RECOMENDACAO] Nenhuma track no YTMusic.")
        return []

    result        = []
    existing_uris = set()

    print(f"\n[SPOTIFY] Buscando {len(ytm_tracks)} tracks...")
    for t in ytm_tracks:
        if len(result) >= 10:
            break

        st = spotify_find_track(t['title'], t['artist'])

        # Se retornou None pode ser 429 — não derruba, só para
        if st is None:
            time.sleep(0.3)
            continue

        uri = st.get('uri')
        if uri and uri not in existing_uris:
            existing_uris.add(uri)
            result.append(st)

        time.sleep(0.1)  # delay entre chamadas para não estourar rate limit

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
        r = requests.get("https://api.spotify.com/v1/me", headers=headers, timeout=8)
        r.raise_for_status()

        mood_label = "Energia Total" if score >= 0.7 else "Vibes Chill" if score >= 0.4 else "Sentimentos"

        playlist_resp = requests.post(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            timeout=8,
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
                timeout=8,
                json={"uris": track_uris}
            ).raise_for_status()

        return playlist["external_urls"]["spotify"]

    except Exception as e:
        print(f"Erro ao criar playlist: {e}")
        return None

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests
import random

# =========================
# AUTENTICAÇÃO SPOTIFY
# =========================
_sp_user = None

def build_sp(access_token):
    global _sp_user
    _sp_user = spotipy.Spotify(auth=access_token)
    return _sp_user

def get_sp():
    auth = SpotifyClientCredentials(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET
    )
    return spotipy.Spotify(auth_manager=auth)


# =========================
# LAST.FM CONFIG
# =========================
LASTFM_API_KEY = settings.LASTFM_API_KEY
LASTFM_BASE    = "https://ws.audioscrobbler.com/2.0/"


# =========================
# MAPEAMENTO GÊNERO
# =========================
GENRE_SEED_MAP = {
    "funk":       "funk",
    "sertanejo":  "sertanejo",
    "pagode":     "pagode",
    "forro":      "forró",
    "forró":      "forró",
    "mpb":        "mpb",
    "samba":      "samba",
    "axe":        "axé",
    "axé":        "axé",
    "rock":       "rock",
    "pop":        "pop",
    "hip-hop":    "hip hop",
    "hip hop":    "hip hop",
    "rap":        "rap",
    "electronic": "eletrônica",
    "eletronica": "eletrônica",
    "eletrônica": "eletrônica",
    "edm":        "eletrônica",
    "jazz":       "jazz",
    "classical":  "clássica",
    "classica":   "clássica",
    "clássica":   "clássica",
    "blues":      "blues",
    "reggaeton":  "reggaeton",
    "r&b":        "r&b",
    "indie":      "indie",
    "metal":      "metal",
    "country":    "country",
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
# TAGS LAST.FM POR MOOD + GÊNERO
# =========================
LASTFM_TAGS = {
    'alto': {
        'funk':       ["baile funk", "funk carioca", "funk brasileiro"],
        'sertanejo':  ["sertanejo", "sertanejo universitario", "forro"],
        'pagode':     ["pagode", "samba", "brazilian music"],
        'forró':      ["forro", "sertanejo", "brazilian music"],
        'mpb':        ["mpb", "bossa nova", "brazilian music"],
        'samba':      ["samba", "pagode", "brazilian music"],
        'axé':        ["axe", "brazilian music"],
        'pop':        ["pop", "dance pop", "feel good"],
        'rock':       ["rock", "classic rock", "alternative rock"],
        'hip hop':    ["hip-hop", "rap", "trap"],
        'eletrônica': ["electronic", "edm", "dance"],
        'jazz':       ["jazz", "swing", "big band"],
        'clássica':   ["classical", "orchestra", "piano"],
        'blues':      ["blues", "blues rock"],
        'reggaeton':  ["reggaeton", "latin"],
        'rap':        ["rap", "hip-hop", "trap"],
        'indie':      ["indie pop", "indie rock"],
        'metal':      ["metal", "heavy metal"],
        'country':    ["country", "country pop"],
        'r&b':        ["r&b", "soul"],
    },
    'medio': {
        'funk':       ["funk melody", "funk"],
        'sertanejo':  ["sertanejo romantico", "sertanejo"],
        'pagode':     ["pagode romantico", "pagode"],
        'forró':      ["forro romantico", "forro"],
        'mpb':        ["mpb", "bossa nova"],
        'samba':      ["bossa nova", "samba jazz"],
        'axé':        ["axe", "brazilian music"],
        'pop':        ["pop", "indie pop", "acoustic pop"],
        'rock':       ["soft rock", "indie rock", "acoustic"],
        'hip hop':    ["lo-fi hip hop", "chill hop"],
        'eletrônica': ["chillwave", "ambient", "lo-fi"],
        'jazz':       ["smooth jazz", "jazz"],
        'clássica':   ["classical", "piano"],
        'blues':      ["blues", "slow blues"],
        'reggaeton':  ["reggaeton romantico", "latin"],
        'rap':        ["rap", "hip-hop"],
        'indie':      ["indie", "dream pop"],
        'metal':      ["progressive metal"],
        'country':    ["country", "acoustic country"],
        'r&b':        ["r&b", "soul", "neo soul"],
    },
    'baixo': {
        'funk':       ["funk sad", "funk melody"],
        'sertanejo':  ["sofrencia", "sertanejo triste", "sertanejo"],
        'pagode':     ["pagode triste", "samba"],
        'forró':      ["forro sofrencia", "forro"],
        'mpb':        ["mpb", "bossa nova"],
        'samba':      ["samba triste", "mpb"],
        'axé':        ["axe", "brazilian music"],
        'pop':        ["sad pop", "heartbreak", "melancholic"],
        'rock':       ["sad rock", "melancholic", "emo"],
        'hip hop':    ["sad rap", "emo rap", "melancholic hip-hop"],
        'eletrônica': ["dark electronic", "melancholic", "ambient"],
        'jazz':       ["jazz blues", "melancholic jazz"],
        'clássica':   ["sad classical", "piano"],
        'blues':      ["blues", "sad blues", "delta blues"],
        'reggaeton':  ["reggaeton triste", "latin"],
        'rap':        ["sad rap", "emo rap"],
        'indie':      ["sad indie", "emo", "melancholic"],
        'metal':      ["doom metal", "gothic metal"],
        'country':    ["sad country", "heartbreak country"],
        'r&b':        ["sad r&b", "soul"],
    },
}




# =========================
# TAGS DE NOSTALGIA POR GÊNERO
# =========================
# Misturadas às tags principais conforme o score de nostalgia.
NOSTALGIA_TAGS = {
    'retro': {  # nostalgia > 60 → músicas antigas/clássicas
        'pop':        ["80s", "90s", "classic pop", "oldies"],
        'rock':       ["classic rock", "70s rock", "80s rock", "90s rock"],
        'hip hop':    ["old school hip hop", "90s hip hop", "classic rap"],
        'eletrônica': ["80s electronic", "synthwave", "retro electronic"],
        'funk':       ["funk soul", "70s funk", "classic funk"],
        'sertanejo':  ["sertanejo raiz", "musica caipira", "sertanejo antigo"],
        'pagode':     ["pagode classico", "samba antigo", "pagode 90s"],
        'forró':      ["forro pe de serra", "forro antigo", "forro raiz"],
        'mpb':        ["mpb classica", "bossa nova", "tropicalia"],
        'samba':      ["samba classico", "bossa nova", "samba antigo"],
        'axé':        ["axe classico", "axe 90s"],
        'jazz':       ["classic jazz", "bebop", "jazz standards"],
        'clássica':   ["baroque", "romantic classical", "classical masterpieces"],
        'blues':      ["delta blues", "chicago blues", "classic blues"],
        'reggaeton':  ["reggaeton old school", "latin classic"],
        'rap':        ["old school rap", "90s rap", "classic hip hop"],
        'indie':      ["90s indie", "indie classic", "alternative 90s"],
        'metal':      ["classic metal", "80s metal", "thrash metal"],
        'country':    ["classic country", "outlaw country", "70s country"],
        'r&b':        ["classic r&b", "soul", "motown"],
    },
    'novo': {  # nostalgia < 40 → músicas recentes
        'pop':        ["pop 2024", "new pop", "trending pop"],
        'rock':       ["modern rock", "rock 2024", "new rock"],
        'hip hop':    ["trap 2024", "new hip hop", "drill"],
        'eletrônica': ["edm 2024", "future bass", "new electronic"],
        'funk':       ["funk 2024", "funk brasileiro novo"],
        'sertanejo':  ["sertanejo 2024", "sertanejo universitario novo"],
        'pagode':     ["pagode 2024", "pagode novo"],
        'forró':      ["forro 2024", "piseiro", "forro novo"],
        'mpb':        ["mpb nova", "mpb 2024"],
        'samba':      ["samba novo", "pagode novo"],
        'axé':        ["axe novo", "axe 2024"],
        'jazz':       ["contemporary jazz", "nu jazz", "jazz fusion"],
        'clássica':   ["contemporary classical", "modern classical"],
        'blues':      ["modern blues", "contemporary blues"],
        'reggaeton':  ["reggaeton 2024", "latin trap"],
        'rap':        ["rap 2024", "trap brasileiro novo"],
        'indie':      ["indie 2024", "new indie", "indie pop novo"],
        'metal':      ["modern metal", "metalcore 2024", "djent"],
        'country':    ["new country", "country pop 2024"],
        'r&b':        ["contemporary r&b", "r&b 2024", "alt r&b"],
    },
}

def get_nostalgia_tags(nostalgia_score, genre_label):
    """
    nostalgia_score: 0-100
    > 60 → retro (clássicos)
    < 40 → novo (lançamentos recentes)
    40-60 → neutro (sem tags extras)
    """
    if nostalgia_score > 60:
        return NOSTALGIA_TAGS['retro'].get(genre_label, [])
    elif nostalgia_score < 40:
        return NOSTALGIA_TAGS['novo'].get(genre_label, [])
    return []  # faixa neutra, não adiciona nada

# =========================
# LAST.FM: TOP TRACKS POR TAG
# =========================
def lastfm_tag_toptracks(tag, limit=50):
    """Busca as top tracks de uma tag no Last.fm."""
    try:
        resp = requests.get(LASTFM_BASE, params={
            "method":  "tag.gettoptracks",
            "tag":     tag,
            "api_key": LASTFM_API_KEY,
            "format":  "json",
            "limit":   limit,
        }, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        tracks = data.get("tracks", {}).get("track", [])
        print(f"[LASTFM] tag='{tag}' -> {len(tracks)} tracks")
        return [{"name": t["name"], "artist": t["artist"]["name"]} for t in tracks if t.get("name")]
    except Exception as e:
        print(f"[LASTFM] Erro tag='{tag}': {e}")
        return []


# =========================
# SPOTIFY: BUSCAR URI POR NOME+ARTISTA
# =========================
def spotify_search_track(name, artist):
    """Busca uma track no Spotify pelo nome+artista vindos do Last.fm."""
    try:
        sp = get_sp()
        # Busca estruturada primeiro
        results = sp.search(q=f"track:{name} artist:{artist}", type="track", limit=1, market="BR")
        items   = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]
        # Fallback simples
        results = sp.search(q=f"{name} {artist}", type="track", limit=1, market="BR")
        items   = results.get("tracks", {}).get("items", [])
        return items[0] if items else None
    except Exception as e:
        print(f"[SPOTIFY] Erro '{name} - {artist}': {e}")
        return None


# =========================
# RECOMENDAÇÃO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    """
    Fluxo:
      1. Score fuzzy → mood (alto/medio/baixo)
      2. Gênero → tags Last.fm
      3. Last.fm tag.gettoptracks → nome+artista
      4. Spotify search → URI + capa para cada track
      5. Retorna top 10
    """
    genre_label = normalize_genre(genre)
    score       = max(0.0, min(float(score), 1.0))
    mood        = get_mood_level(score)
    data        = data or {}

    tags      = LASTFM_TAGS.get(mood, {}).get(genre_label, [genre_label])
    nostalgia = float(data.get('nostalgia', 50))
    nos_tags  = get_nostalgia_tags(nostalgia, genre_label)

    # Intercala tags de nostalgia com as tags principais
    # Limita a 4 tags no total para controlar chamadas à API
    combined_tags = []
    nos_iter = iter(nos_tags)
    for i, tag in enumerate(tags):
        combined_tags.append(tag)
        if i % 2 == 0:
            nt = next(nos_iter, None)
            if nt:
                combined_tags.append(nt)
    tags = combined_tags[:4]  # máximo 4 tags → máximo 40 tracks do Last.fm → máximo 15 chamadas Spotify

    print(f"\n{'='*50}")
    print(f"[RECOMENDACAO] Gênero: {genre_label} | Score: {score:.2f} | Mood: {mood} | Nostalgia: {nostalgia:.0f}")
    print(f"[RECOMENDACAO] Tags Last.fm: {tags}")
    print(f"{'='*50}")

    # Coleta tracks do Last.fm sem duplicatas
    # Limita a 10 por tag para reduzir chamadas ao Spotify
    seen_keys     = set()
    lastfm_tracks = []

    for tag in tags:
        tracks = lastfm_tag_toptracks(tag, limit=10)  # 10 por tag (antes era 50)
        random.shuffle(tracks)
        for t in tracks:
            key = f"{t['name'].lower()}|{t['artist'].lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                lastfm_tracks.append(t)

    print(f"[LASTFM TOTAL] {len(lastfm_tracks)} tracks únicas")

    # Fallback se Last.fm não retornou nada
    if not lastfm_tracks:
        print("[FALLBACK] Last.fm vazio, buscando direto no Spotify...")
        try:
            sp      = get_sp()
            results = sp.search(q=f"{genre_label} {mood}", type="track", limit=10, market="BR")
            return results.get("tracks", {}).get("items", [])
        except Exception as e:
            print(f"[FALLBACK] Erro: {e}")
            return []

    # Busca no Spotify em batch: monta queries múltiplas num único search
    # "track:A artist:X OR track:B artist:Y" não é suportado,
    # então usamos sp.search com q combinado para cada par nome+artista,
    # mas limitamos a no máximo 15 chamadas com delay entre elas.
    import time
    result     = []
    candidates = lastfm_tracks[:30] # máximo 15 candidatos → máximo 15 chamadas

    for t in candidates:
        if len(result) >= 20:
            break
        spotify_track = spotify_search_track(t["name"], t["artist"])
        if spotify_track:
            result.append(spotify_track)
            print(f"  ✔ {spotify_track['name']} - {spotify_track['artists'][0]['name']}")
        else:
            print(f"  ✘ Não encontrado: {t['name']} - {t['artist']}")
        time.sleep(0.2)  # 200ms entre chamadas evita burst que causa rate limit

    print(f"\n[RESULTADO] {len(result)} músicas")
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

        mood_label = "Energia Total 🔥" if score >= 0.7 else "Vibes Chill 🌊" if score >= 0.4 else "Sentimentos 💜"

        playlist_resp = requests.post(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            json={
                "name":        f"HarmonAI — {genre.title()} | {mood_label}",
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
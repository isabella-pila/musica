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


# =========================
# MAPEAMENTO GENERO
# =========================
GENRE_SEED_MAP = {
    "funk":       "funk",
    "sertanejo":  "sertanejo",
    "pagode":     "pagode",
    "forro":      "forro",
    "mpb":        "mpb",
    "samba":      "samba",
    "axe":        "axe",
    "rock":       "rock",
    "pop":        "pop",
    "hip-hop":    "hip hop",
    "hip hop":    "hip hop",
    "rap":        "rap",
    "electronic": "eletronica",
    "eletronica": "eletronica",
    "edm":        "eletronica",
    "jazz":       "jazz",
    "classical":  "classica",
    "classica":   "classica",
    "blues":      "blues",
    "reggaeton":  "reggaeton",
    "r&b":        "rnb",
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
# LABELS PARA FRONTEND
# =========================
def get_popularity_label(value):
    """Retorna label descritivo para o nivel de popularidade (0-100)."""
    if value >= 75:
        return "Viral / Famosa"
    elif value >= 50:
        return "Popular"
    elif value >= 25:
        return "Moderada"
    return "Underground"

def get_nostalgia_label(value):
    """Retorna label descritivo para o nivel de nostalgia (0-100)."""
    if value >= 75:
        return "Classicos"
    elif value >= 50:
        return "Retro"
    elif value >= 25:
        return "Mix"
    return "Lancamentos"


# =========================
# ARTISTAS CONHECIDOS POR GENERO (FALLBACK CONFIAVEL)
# =========================
GENRE_ARTISTS = {
    'funk':       ["MC Kevin o Chris", "Anitta", "Pedro Sampaio", "MC Livinho", "Ludmilla", "MC Don Juan", "Dennis DJ", "MC Kevinho", "Mc Cabelinho", "Mc Hariel"],
    'sertanejo':  ["Gusttavo Lima", "Jorge & Mateus", "Henrique e Juliano", "Maiara e Maraisa", "Luan Santana", "Leonardo", "Simone Mendes", "Zeze Di Camargo & Luciano"],
    'pagode':     ["Thiaguinho", "Grupo Revelacao", "Pericles", "Sorriso Maroto", "Ferrugem", "Dilsinho", "Turma do Pagode", "Menos E Mais", "Belo", "Alexandre Pires"],
    'forro':      ["Luiz Gonzaga", "Wesley Safadao", "Xand Aviao", "Falamansa", "Calcinha Preta", "Joao Gomes", "Ze Vaqueiro", "Mari Fernandez"],
    'mpb':        ["Caetano Veloso", "Gilberto Gil", "Djavan", "Maria Bethania", "Marisa Monte", "Chico Buarque", "Tim Maia", "Elis Regina", "Jorge Ben Jor", "Gal Costa"],
    'samba':      ["Beth Carvalho", "Zeca Pagodinho", "Martinho da Vila", "Clara Nunes", "Paulinho da Viola", "Jorge Aragao", "Alcione", "Arlindo Cruz", "Cartola", "Fundo de Quintal"],
    'axe':        ["Ivete Sangalo", "Claudia Leitte", "Bell Marques", "Chiclete com Banana", "Daniela Mercury", "Olodum", "Timbalada", "Banda Eva"],
    'pop':        ["Taylor Swift", "The Weeknd", "Dua Lipa", "Harry Styles", "Billie Eilish", "Ed Sheeran", "Ariana Grande", "Bruno Mars", "Adele", "Lady Gaga"],
    'rock':       ["Foo Fighters", "Arctic Monkeys", "Red Hot Chili Peppers", "Nirvana", "Queen", "The Beatles", "Pink Floyd", "AC/DC", "Led Zeppelin", "Imagine Dragons"],
    'hip hop':    ["Kendrick Lamar", "Drake", "Travis Scott", "Kanye West", "J. Cole", "Tyler, The Creator", "Post Malone", "21 Savage", "Eminem", "Jay-Z"],
    'eletronica': ["David Guetta", "Calvin Harris", "Marshmello", "Martin Garrix", "Alok", "Vintage Culture", "Daft Punk", "Skrillex", "Deadmau5"],
    'jazz':       ["Miles Davis", "John Coltrane", "Bill Evans", "Thelonious Monk", "Charlie Parker", "Duke Ellington", "Louis Armstrong", "Nina Simone", "Herbie Hancock", "Chet Baker"],
    'classica':   ["Ludwig van Beethoven", "Wolfgang Amadeus Mozart", "Johann Sebastian Bach", "Frederic Chopin", "Antonio Vivaldi", "Claude Debussy", "Franz Schubert"],
    'blues':      ["B.B. King", "Muddy Waters", "Robert Johnson", "Stevie Ray Vaughan", "John Lee Hooker", "Eric Clapton", "Buddy Guy"],
    'reggaeton':  ["Bad Bunny", "J Balvin", "Daddy Yankee", "Ozuna", "Maluma", "Rauw Alejandro", "Karol G"],
    'rap':        ["Emicida", "Djonga", "Filipe Ret", "Matue", "Xama", "L7nnon", "Costa Gold", "Criolo"],
    'indie':      ["Arctic Monkeys", "Tame Impala", "Mac DeMarco", "Radiohead", "The Strokes", "Vampire Weekend", "Beach House", "Bon Iver"],
    'metal':      ["Metallica", "Iron Maiden", "Black Sabbath", "Slayer", "Megadeth", "Judas Priest", "Pantera", "Sepultura"],
    'country':    ["Morgan Wallen", "Luke Combs", "Chris Stapleton", "Zach Bryan", "Luke Bryan", "Carrie Underwood", "Blake Shelton", "Kenny Chesney"],
    'rnb':        ["The Weeknd", "SZA", "Frank Ocean", "Daniel Caesar", "H.E.R.", "Chris Brown", "Usher"],
}


# =========================
# QUERY SPOTIFY POR GENERO (para busca direta no Spotify)
# =========================
GENRE_SPOTIFY_QUERY = {
    'funk':       "funk brasileiro",
    'sertanejo':  "sertanejo",
    'pagode':     "pagode",
    'forro':      "forro",
    'mpb':        "mpb",
    'samba':      "samba",
    'axe':        "axe bahia",
    'pop':        "pop",
    'rock':       "rock",
    'hip hop':    "hip hop",
    'eletronica': "electronic dance",
    'jazz':       "jazz",
    'classica':   "classical",
    'blues':      "blues",
    'reggaeton':  "reggaeton",
    'rap':        "rap brasileiro",
    'indie':      "indie",
    'metal':      "metal",
    'country':    "country",
    'rnb':        "r&b",
}


# =========================
# TAGS LAST.FM POR MOOD + GENERO
# =========================
LASTFM_TAGS = {
    'alto': {
        'funk':       ["baile funk", "funk carioca", "funk brasileiro"],
        'sertanejo':  ["sertanejo", "sertanejo universitario", "forro"],
        'pagode':     ["pagode", "samba", "brazilian music"],
        'forro':      ["forro", "sertanejo", "brazilian music"],
        'mpb':        ["mpb", "bossa nova", "brazilian music"],
        'samba':      ["samba", "pagode", "brazilian music"],
        'axe':        ["axe", "brazilian music"],
        'pop':        ["pop", "dance pop", "feel good"],
        'rock':       ["rock", "classic rock", "alternative rock"],
        'hip hop':    ["hip-hop", "rap", "trap"],
        'eletronica': ["electronic", "edm", "dance"],
        'jazz':       ["jazz", "swing", "big band"],
        'classica':   ["classical", "orchestra", "piano"],
        'blues':      ["blues", "blues rock"],
        'reggaeton':  ["reggaeton", "latin"],
        'rap':        ["rap", "hip-hop", "trap"],
        'indie':      ["indie pop", "indie rock"],
        'metal':      ["metal", "heavy metal"],
        'country':    ["country", "country pop"],
        'rnb':        ["rnb", "r&b", "soul"],
    },
    'medio': {
        'funk':       ["funk melody", "funk"],
        'sertanejo':  ["sertanejo romantico", "sertanejo"],
        'pagode':     ["pagode romantico", "pagode"],
        'forro':      ["forro romantico", "forro"],
        'mpb':        ["mpb", "bossa nova"],
        'samba':      ["bossa nova", "samba jazz"],
        'axe':        ["axe", "brazilian music"],
        'pop':        ["pop", "indie pop", "acoustic pop"],
        'rock':       ["soft rock", "indie rock", "acoustic"],
        'hip hop':    ["lo-fi hip hop", "chill hop"],
        'eletronica': ["chillwave", "ambient", "lo-fi"],
        'jazz':       ["smooth jazz", "jazz"],
        'classica':   ["classical", "piano"],
        'blues':      ["blues", "slow blues"],
        'reggaeton':  ["reggaeton romantico", "latin"],
        'rap':        ["rap", "hip-hop"],
        'indie':      ["indie", "dream pop"],
        'metal':      ["progressive metal"],
        'country':    ["country", "acoustic country"],
        'rnb':        ["rnb", "r&b", "soul", "neo soul"],
    },
    'baixo': {
        'funk':       ["funk sad", "funk melody"],
        'sertanejo':  ["sofrencia", "sertanejo triste", "sertanejo"],
        'pagode':     ["pagode triste", "samba"],
        'forro':      ["forro sofrencia", "forro"],
        'mpb':        ["mpb", "bossa nova"],
        'samba':      ["samba triste", "mpb"],
        'axe':        ["axe", "brazilian music"],
        'pop':        ["sad pop", "heartbreak", "melancholic"],
        'rock':       ["sad rock", "melancholic", "emo"],
        'hip hop':    ["sad rap", "emo rap", "melancholic hip-hop"],
        'eletronica': ["dark electronic", "melancholic", "ambient"],
        'jazz':       ["jazz blues", "melancholic jazz"],
        'classica':   ["sad classical", "piano"],
        'blues':      ["blues", "sad blues", "delta blues"],
        'reggaeton':  ["reggaeton triste", "latin"],
        'rap':        ["sad rap", "emo rap"],
        'indie':      ["sad indie", "emo", "melancholic"],
        'metal':      ["doom metal", "gothic metal"],
        'country':    ["sad country", "heartbreak country"],
        'rnb':        ["sad r&b", "soul"],
    },
}


# =========================
# TAGS DE NOSTALGIA POR GENERO
# =========================
NOSTALGIA_TAGS = {
    'retro': {
        'pop':        ["80s", "90s", "classic pop", "oldies"],
        'rock':       ["classic rock", "70s rock", "80s rock", "90s rock"],
        'hip hop':    ["old school hip hop", "90s hip hop", "classic rap"],
        'eletronica': ["80s electronic", "synthwave", "retro electronic"],
        'funk':       ["funk soul", "70s funk", "classic funk"],
        'sertanejo':  ["sertanejo raiz", "musica caipira", "sertanejo antigo"],
        'pagode':     ["pagode classico", "samba antigo", "pagode 90s"],
        'forro':      ["forro pe de serra", "forro antigo", "forro raiz"],
        'mpb':        ["mpb classica", "bossa nova", "tropicalia"],
        'samba':      ["samba classico", "bossa nova", "samba antigo"],
        'axe':        ["axe classico", "axe 90s"],
        'jazz':       ["classic jazz", "bebop", "jazz standards"],
        'classica':   ["baroque", "romantic classical", "classical masterpieces"],
        'blues':      ["delta blues", "chicago blues", "classic blues"],
        'reggaeton':  ["reggaeton old school", "latin classic"],
        'rap':        ["old school rap", "90s rap", "classic hip hop"],
        'indie':      ["90s indie", "indie classic", "alternative 90s"],
        'metal':      ["classic metal", "80s metal", "thrash metal"],
        'country':    ["classic country", "outlaw country", "70s country"],
        'rnb':        ["classic r&b", "soul", "motown"],
    },
    'novo': {
        'pop':        ["pop 2024", "new pop", "trending pop"],
        'rock':       ["modern rock", "rock 2024", "new rock"],
        'hip hop':    ["trap 2024", "new hip hop", "drill"],
        'eletronica': ["edm 2024", "future bass", "new electronic"],
        'funk':       ["funk 2024", "funk brasileiro novo"],
        'sertanejo':  ["sertanejo 2024", "sertanejo universitario novo"],
        'pagode':     ["pagode 2024", "pagode novo"],
        'forro':      ["forro 2024", "piseiro", "forro novo"],
        'mpb':        ["mpb nova", "mpb 2024"],
        'samba':      ["samba novo", "pagode novo"],
        'axe':        ["axe novo", "axe 2024"],
        'jazz':       ["contemporary jazz", "nu jazz", "jazz fusion"],
        'classica':   ["contemporary classical", "modern classical"],
        'blues':      ["modern blues", "contemporary blues"],
        'reggaeton':  ["reggaeton 2024", "latin trap"],
        'rap':        ["rap 2024", "trap brasileiro novo"],
        'indie':      ["indie 2024", "new indie", "indie pop novo"],
        'metal':      ["modern metal", "metalcore 2024", "djent"],
        'country':    ["new country", "country pop 2024"],
        'rnb':        ["contemporary r&b", "r&b 2024", "alt r&b"],
    },
}

def get_nostalgia_tags(nostalgia_score, genre_label):
    """
    nostalgia_score: 0-100
    > 60 = retro (classicos)
    < 40 = novo (lancamentos recentes)
    40-60 = neutro (sem tags extras)
    """
    if nostalgia_score > 60:
        return NOSTALGIA_TAGS['retro'].get(genre_label, [])
    elif nostalgia_score < 40:
        return NOSTALGIA_TAGS['novo'].get(genre_label, [])
    return []


# =========================
# POPULARIDADE -> PAGINA DO LAST.FM
# =========================
def get_lastfm_page_for_popularity(popularity):
    """Mapeia o slider de popularidade (0-100) para a pagina do ranking Last.fm."""
    if popularity >= 75:
        return 1
    elif popularity >= 50:
        return 2
    elif popularity >= 25:
        return 3
    else:
        return 5


# =========================
# LAST.FM: TOP TRACKS POR TAG
# =========================
def lastfm_tag_toptracks(tag, limit=50, page=1):
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
def lastfm_tag_topartists(tag, limit=10, page=1):
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
    """Busca tracks diretamente no Spotify pelo genero traduzido."""
    try:
        sp = get_sp()
        query = GENRE_SPOTIFY_QUERY.get(genre_label, genre_label)
        results = sp.search(q=f"genre:{query}", type="track", limit=limit, market="BR")
        items = results.get("tracks", {}).get("items", [])
        print(f"[SPOTIFY GENRE] query='genre:{query}' -> {len(items)} tracks")
        return items
    except Exception as e:
        print(f"[SPOTIFY GENRE] Erro: {e}")
        return []


# =========================
# FILTRO DE NOSTALGIA POR ANO
# =========================
def passes_nostalgia_filter(spotify_track, nostalgia_score):
    """Filtra tracks do Spotify pela data de lancamento baseado no score de nostalgia."""
    if 40 <= nostalgia_score <= 60:
        return True

    try:
        release_date = spotify_track.get("album", {}).get("release_date", "")
        if not release_date:
            return True
        year = int(release_date[:4])
    except (ValueError, IndexError):
        return True

    if nostalgia_score > 60:
        return year <= 2015
    elif nostalgia_score < 40:
        return year >= 2018

    return True


# =========================
# RECOMENDACAO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    """
    Fluxo com 3 camadas para garantir musicas do genero correto:
    
      CAMADA 1: Last.fm tag.gettoptracks (tags de mood+genero)
      CAMADA 2: Last.fm artist.gettoptracks (artistas conhecidos do genero)
      CAMADA 3: Spotify search por genero (fallback final)
    """
    genre_label = normalize_genre(genre)
    score       = max(0.0, min(float(score), 1.0))
    mood        = get_mood_level(score)
    data        = data or {}

    popularity = float(data.get('popularity', 50))
    nostalgia  = float(data.get('nostalgia', 50))

    # Tags base do mood
    mood_tags = LASTFM_TAGS.get(mood, {}).get(genre_label, [genre_label])

    # Tags de nostalgia (complementares)
    nos_tags = get_nostalgia_tags(nostalgia, genre_label)

    # Combinar tags: priorizar mood, depois 1 tag de nostalgia
    combined_tags = list(mood_tags)
    if nos_tags:
        combined_tags.append(nos_tags[0])
    tags = combined_tags[:4]

    # Pagina do Last.fm baseada na popularidade
    lastfm_page = get_lastfm_page_for_popularity(popularity)

    print(f"\n{'='*60}")
    print(f"[RECOMENDACAO] Genero: {genre_label} | Score: {score:.2f} | Mood: {mood}")
    print(f"[RECOMENDACAO] Popularidade: {popularity:.0f}% ({get_popularity_label(popularity)}) -> page={lastfm_page}")
    print(f"[RECOMENDACAO] Nostalgia: {nostalgia:.0f}% ({get_nostalgia_label(nostalgia)})")
    print(f"[RECOMENDACAO] Tags Last.fm: {tags}")
    print(f"{'='*60}")

    seen_keys     = set()
    lastfm_tracks = []

    # ========================================
    # CAMADA 1: Last.fm tag.gettoptracks
    # ========================================
    print(f"\n--- CAMADA 1: tag.gettoptracks ---")
    for tag in tags:
        tracks = lastfm_tag_toptracks(tag, limit=20, page=lastfm_page)
        for t in tracks:
            key = f"{t['name'].lower()}|{t['artist'].lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                lastfm_tracks.append(t)

    print(f"[CAMADA 1] {len(lastfm_tracks)} tracks das tags")

    # ========================================
    # CAMADA 2: Last.fm artist.gettoptracks
    # ========================================
    print(f"\n--- CAMADA 2: artist.gettoptracks (artistas do genero) ---")
    
    # Buscar artistas via Last.fm tag
    primary_tag = tags[0] if tags else genre_label
    genre_artists_from_lastfm = lastfm_tag_topartists(primary_tag, limit=8, page=lastfm_page)

    # Complementa com artistas hardcoded do genero
    known_artists = GENRE_ARTISTS.get(genre_label, [])
    
    # Combina: artistas do Last.fm primeiro, depois os conhecidos
    all_genre_artists = []
    seen_artists = set()
    for a in genre_artists_from_lastfm + known_artists:
        a_lower = a.lower()
        if a_lower not in seen_artists:
            seen_artists.add(a_lower)
            all_genre_artists.append(a)
    
    # Limita a 6 artistas
    artists_to_query = all_genre_artists[:6]

    for artist_name in artists_to_query:
        tracks = lastfm_artist_toptracks(artist_name, limit=5)
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
    result     = []
    candidates = lastfm_tracks[:50]

    for t in candidates:
        if len(result) >= 10:
            break
        try:
            spotify_track = spotify_search_track(t["name"], t["artist"])
            if spotify_track:
                if passes_nostalgia_filter(spotify_track, nostalgia):
                    result.append(spotify_track)
                    release = spotify_track.get("album", {}).get("release_date", "?")
                    artist_name = spotify_track['artists'][0]['name']
                    safe_print(f"  [OK] {spotify_track['name']} - {artist_name} ({release})")
                else:
                    release = spotify_track.get("album", {}).get("release_date", "?")
                    safe_print(f"  [SKIP] Filtrado por nostalgia: {spotify_track['name']} ({release})")
            else:
                safe_print(f"  [X] Nao encontrado: {t['name']} - {t['artist']}")
        except spotipy.SpotifyException as e:
            if getattr(e, 'http_status', None) == 429:
                print("[WAIT] Rate Limit do Spotify atingido.")
                break
        time.sleep(0.1)

    # ========================================
    # CAMADA 3: Spotify search por genero
    # ========================================
    if len(result) < 10:
        print(f"\n--- CAMADA 3: Spotify search por genero (faltam {10 - len(result)} tracks) ---")
        existing_uris = {r.get('uri') for r in result}
        
        spotify_genre_tracks = spotify_search_genre(genre_label, mood, limit=15)
        for st in spotify_genre_tracks:
            if len(result) >= 10:
                break
            if st.get('uri') not in existing_uris:
                if passes_nostalgia_filter(st, nostalgia):
                    result.append(st)
                    existing_uris.add(st.get('uri'))
                    safe_print(f"  [OK] (genero) {st['name']} - {st['artists'][0]['name']}")

    # Se ainda nao tem o suficiente, relaxar filtro de nostalgia
    if len(result) < 5:
        print(f"\n[RELAXANDO FILTRO] Apenas {len(result)} tracks, buscando sem filtro de data...")
        existing_uris = {r.get('uri') for r in result}
        
        spotify_genre_tracks = spotify_search_genre(genre_label, mood, limit=20)
        for st in spotify_genre_tracks:
            if len(result) >= 10:
                break
            if st.get('uri') not in existing_uris:
                result.append(st)
                existing_uris.add(st.get('uri'))
                safe_print(f"  [OK] (relaxado) {st['name']} - {st['artists'][0]['name']}")

    print(f"\n[RESULTADO FINAL] {len(result)} musicas do genero '{genre_label}'")
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
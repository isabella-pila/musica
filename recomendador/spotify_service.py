import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests
import random

auth_manager = SpotifyClientCredentials(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)


# =====================================================================
# NOTA IMPORTANTE (Abril 2026):
# A Spotify Web API removeu o campo "popularity" em fev/2026.
# O endpoint sp.tracks() retorna 403 com ClientCredentials.
# O limit maximo do search agora eh 10.
#
# Estrategia adaptada:
# - Popularidade: controlada via queries (ex: "top hits" vs "underground")
# - Nostalgia: controlada via filtro year: na query
# - Busca combina resultados de multiplas queries para mais variedade
# - Deduplicacao por track ID impede repeticoes
# =====================================================================


# =========================
# NOSTALGIA -> FILTRO DE ANO
# =========================
def nostalgia_year_filter(nosta):
    """Traduz nostalgia (0-1) em filtro year: do Spotify."""
    if nosta >= 0.8:
        return "year:1960-1989"
    elif nosta >= 0.6:
        return "year:1990-2009"
    elif nosta >= 0.4:
        return ""
    elif nosta >= 0.2:
        return "year:2018-2024"
    else:
        return "year:2024-2026"


# =========================
# SCORE -> MOOD TAGS
# =========================
def score_to_tags(score, genre):
    """
    Retorna uma LISTA de tags curtas para busca.
    Tags curtas funcionam melhor no Spotify do que frases longas.
    Frases longas fazem o Spotify buscar por nome literal.
    """
    # Tags especificas por genero + score
    genre_tags = {
        "rock": {
            0.80: ["hard rock", "rock anthem", "rock energy"],
            0.60: ["rock", "alternative rock", "classic rock"],
            0.40: ["indie rock", "acoustic rock", "soft rock"],
            0.00: ["sad rock"],
        },
        "pop": {
            0.80: ["dance pop", "pop hits", "party pop"],
            0.60: ["pop", "synth pop", "electropop"],
            0.40: ["acoustic pop", "indie pop", "chill pop"],
            0.00: ["sad pop", "dark pop", "slow pop"],
        },
        "hip-hop": {
            0.80: ["trap", "hype rap", "rap hits"],
            0.60: ["hip hop", "rap", "boom bap"],
            0.40: ["lo-fi hip hop", "chill rap", "conscious rap"],
            0.00: ["emo rap", "dark rap", "sad rap"],
        },
        "electronic": {
            0.80: ["EDM", "house music", "dance music"],
            0.60: ["electronic", "synthwave", "progressive house"],
            0.40: ["chillwave", "downtempo", "ambient electronic"],
            0.00: ["dark ambient", "drone", "dark electronic"],
        },
        "jazz": {
            0.80: ["swing jazz", "big band", "latin jazz"],
            0.60: ["smooth jazz", "jazz", "bossa nova"],
            0.40: ["cool jazz", "jazz piano", "jazz ballad"],
            0.00: ["dark jazz", "noir jazz", "melancholy jazz"],
        },
        "classical": {
            0.80: ["orchestral", "symphony", "triumphant classical"],
            0.60: ["classical", "romantic classical", "violin classical"],
            0.40: ["piano classical", "calm classical", "chamber music"],
            0.00: ["requiem", "somber classical", "funeral march"],
        },
        "blues": {
            0.80: ["electric blues", "blues rock", "upbeat blues"],
            0.60: ["blues", "rhythm and blues", "chicago blues"],
            0.40: ["acoustic blues", "slow blues", "folk blues"],
            0.00: ["delta blues", "sad blues", "dark blues"],
        },
    }

    # Encontra o nivel de score adequado
    tags_by_level = genre_tags.get(genre, {})
    for threshold in [0.80, 0.60, 0.40, 0.00]:
        if score >= threshold:
            return tags_by_level.get(threshold, [genre])

    return [genre]


# =========================
# BUSCA COM DEDUPLICACAO
# =========================
def _search_tracks(query, seen_ids=None):
    """
    Busca tracks no Spotify (limit=10, maximo da API).
    Retorna apenas tracks cujo ID nao esta em seen_ids (deduplicacao).
    """
    if seen_ids is None:
        seen_ids = set()

    try:
        # Offset aleatorio para variedade (entre 0 e 20)
        offset = random.randint(0, 2) * 10
        results = sp.search(q=query, type="track", limit=10, offset=offset, market="US")
        tracks = results.get("tracks", {}).get("items", [])

        if not tracks and offset > 0:
            # Se nao encontrou com offset, tenta sem
            results = sp.search(q=query, type="track", limit=10, offset=0, market="US")
            tracks = results.get("tracks", {}).get("items", [])

        # Deduplicar
        unique = []
        for t in tracks:
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                unique.append(t)

        return unique

    except Exception as e:
        print(f"Erro em _search_tracks ({query}): {e}")
        return []


# =========================
# BUSCA POR ARTISTAS DO GENERO (FALLBACK)
# =========================
def _search_by_artists(genre, year_filter="", seen_ids=None):
    """Fallback: busca artistas do genero e pega tracks deles."""
    if seen_ids is None:
        seen_ids = set()

    try:
        results = sp.search(q=f"genre:{genre}", type="artist", limit=5, market="US")
        artists = results.get("artists", {}).get("items", [])

        if not artists:
            return []

        all_tracks = []
        for artist in artists[:4]:
            artist_name = artist.get("name", "")
            if not artist_name:
                continue

            try:
                q = f"artist:{artist_name}"
                if year_filter:
                    q += f" {year_filter}"

                artist_results = sp.search(q=q, type="track", limit=5, market="US")
                for t in artist_results.get("tracks", {}).get("items", []):
                    tid = t.get("id")
                    if tid and tid not in seen_ids:
                        seen_ids.add(tid)
                        all_tracks.append(t)
            except Exception:
                continue

        return all_tracks

    except Exception as e:
        print(f"Erro em _search_by_artists ({genre}): {e}")
        return []


# =========================
# RECOMENDACAO PRINCIPAL
# =========================
def get_recommendations(score, genre, data=None):
    genre = (genre or "").strip().lower()

    VALID_GENRES = ["rock", "pop", "hip-hop", "electronic", "jazz", "classical", "blues"]
    if genre not in VALID_GENRES:
        genre = "pop"

    score = max(0.0, min(float(score), 1.0))
    data = data or {}

    # ---- Extrair parametros ----
    nosta = float(data.get('nostalgia', 0.5))
    pop = float(data.get('popularity', 50))

    tags = score_to_tags(score, genre)
    year_filter = nostalgia_year_filter(nosta)

    print(f"[FUZZY] TAGS: {tags} | SCORE: {score:.2f} | GENRE: {genre}")
    print(f"[FILTROS] POP: {pop} | NOSTALGIA: {nosta} -> {year_filter or 'qualquer epoca'}")

    # ---- Construir queries usando genre: filter do Spotify ----
    # O Spotify Search aceita "genre:" como filtro real, nao como texto livre
    queries = []

    for tag in tags:
        # Tag + filtro de ano (mais especifico)
        if year_filter:
            queries.append(f"genre:{genre} {tag} {year_filter}")

        # Tag + genero (sem ano)
        # So adiciona "genre:" se a tag nao contem o nome do genero
        if genre not in tag.lower():
            queries.append(f"genre:{genre} {tag}")
        else:
            queries.append(tag)

    # Queries extras baseadas em popularidade
    if pop >= 75:
        if year_filter:
            queries.append(f"genre:{genre} {year_filter}")
        queries.append(f"genre:{genre} hits")
        queries.append(f"best of {genre}")
    elif pop < 25:
        queries.append(f"genre:{genre} underground")
        queries.append(f"genre:{genre} indie")

    # Fallback generico
    queries.append(f"genre:{genre}")

    # Remover duplicatas mantendo ordem
    seen_queries = set()
    unique_queries = []
    for q in queries:
        q = q.strip()
        if q and q not in seen_queries:
            seen_queries.add(q)
            unique_queries.append(q)

    # ---- COMBINAR resultados de multiplas queries para variedade ----
    seen_ids = set()
    all_tracks = []

    for q in unique_queries:
        print(f"  Buscando: '{q}'")
        tracks = _search_tracks(q, seen_ids)

        if tracks:
            print(f"    + {len(tracks)} novas musicas")
            all_tracks.extend(tracks)

        # Se ja temos 15+, acumulamos o suficiente
        if len(all_tracks) >= 15:
            break

    # ---- Fallback: artistas do genero ----
    if len(all_tracks) < 5:
        print(f"  Fallback: artistas de '{genre}'...")
        artist_tracks = _search_by_artists(genre, year_filter, seen_ids)
        if artist_tracks:
            print(f"    + {len(artist_tracks)} musicas de artistas")
            all_tracks.extend(artist_tracks)

    # ---- Fallback final ----
    if not all_tracks:
        print("  Fallback final: busca generica...")
        all_tracks = _search_tracks(genre, seen_ids)

    if not all_tracks:
        print("[AVISO] Nenhuma musica encontrada")
        return []

    # ---- Selecionar e embaralhar ----
    # Para popularidade baixa, prefere os ultimos resultados (menos conhecidos)
    if pop < 30:
        all_tracks = list(reversed(all_tracks))

    # Embaralha para nao repetir a mesma ordem
    random.shuffle(all_tracks)

    result = all_tracks[:10]

    print(f"  [RESULTADO] {len(result)} musicas selecionadas de {len(all_tracks)} candidatas:")
    _log_tracks(result)

    return result


def _log_tracks(tracks):
    """Imprime as tracks encontradas para debug."""
    for t in tracks[:5]:
        name = t.get("name", "?")
        artist = t.get("artists", [{}])[0].get("name", "?")
        year = t.get("album", {}).get("release_date", "??")[:4]
        print(f"    -> {name} - {artist} (ano={year})")


# =========================
# CRIAR PLAYLIST
# =========================
def create_playlist(token, track_uris, score, genre):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    requests.get("https://api.spotify.com/v1/me", headers=headers).raise_for_status()

    playlist_resp = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json={
            "name":        f"FuzzyMood - {genre.title()} ({round(score * 100)}%)",
            "public":      True,
            "description": f"Playlist gerada pelo FuzzyMood. Score: {round(score, 3)}"
        }
    )
    playlist_resp.raise_for_status()
    playlist = playlist_resp.json()

    requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist['id']}/items",
        headers=headers,
        json={"uris": track_uris}
    ).raise_for_status()

    return playlist["external_urls"]["spotify"]
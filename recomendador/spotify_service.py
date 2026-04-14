import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings
import requests

auth_manager = SpotifyClientCredentials(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)


def popularity_range(data):
    """
    Usa popularity (0-100) e nostalgia (0-1) do formulário
    para definir a faixa de popularidade das tracks.
    """
    pop   = float(data.get('popularity', 50))
    nosta = float(data.get('nostalgia', 0.5))

    # Clássico + muito popular = hinos consagrados
    if nosta >= 0.7 and pop >= 70:
        return (75, 100)

    # Clássico + médio = conhecidos mas não mainstream
    if nosta >= 0.7 and 40 <= pop < 70:
        return (50, 75)

    # Clássico + baixo = cult obscuro antigo
    if nosta >= 0.7 and pop < 40:
        return (10, 45)

    # Lançamento + muito popular = hits atuais
    if nosta <= 0.3 and pop >= 70:
        return (70, 100)

    # Lançamento + baixo = underground novo
    if nosta <= 0.3 and pop < 40:
        return (0, 35)

    # Popularidade alta genérica
    if pop >= 75:
        return (70, 100)

    # Popularidade média-alta
    if pop >= 55:
        return (50, 80)

    # Popularidade média
    if pop >= 35:
        return (30, 65)

    # Popularidade baixa
    if pop >= 15:
        return (10, 40)

    # Underground total
    return (0, 25)


def filter_by_popularity(tracks, pop_min, pop_max):
    """Filtra tracks pela faixa de popularidade. Se sobrar menos de 3, retorna tudo."""
    filtered = [t for t in tracks if pop_min <= t["popularity"] <= pop_max]
    return filtered if len(filtered) >= 3 else tracks


def score_to_mood(score, genre):
    if score >= 0.80:
        moods = {
            "rock":       "energetic hard rock anthem",
            "pop":        "euphoric dance pop banger",
            "hip-hop":    "hype trap banger",
            "electronic": "festival EDM drop",
            "jazz":       "upbeat swing jazz",
            "classical":  "triumphant orchestral",
            "blues":      "upbeat electric blues",
        }
    elif score >= 0.60:
        moods = {
            "rock":       "indie alternative rock",
            "pop":        "feel good pop",
            "hip-hop":    "conscious rap flow",
            "electronic": "progressive house",
            "jazz":       "smooth jazz groove",
            "classical":  "romantic classical piano",
            "blues":      "soulful blues",
        }
    elif score >= 0.40:
        moods = {
            "rock":       "mellow rock",
            "pop":        "soft acoustic pop",
            "hip-hop":    "lo-fi hip hop",
            "electronic": "ambient downtempo",
            "jazz":       "late night jazz",
            "classical":  "calm classical strings",
            "blues":      "slow acoustic blues",
        }
    elif score >= 0.20:
        moods = {
            "rock":       "melancholic rock ballad",
            "pop":        "sad emotional pop",
            "hip-hop":    "introspective sad rap",
            "electronic": "dark synthwave",
            "jazz":       "melancholic jazz noir",
            "classical":  "somber classical",
            "blues":      "deep slow blues",
        }
    else:
        moods = {
            "rock":       "post punk dark depressive rock",
            "pop":        "dark sad indie pop",
            "hip-hop":    "dark introspective rap",
            "electronic": "dark ambient drone",
            "jazz":       "noir melancholic jazz",
            "classical":  "somber requiem",
            "blues":      "deep dark delta blues",
        }

    return moods.get(genre, f"{genre} music")


def get_recommendations(score, genre, data=None):
    genre = (genre or "").strip().lower()

    VALID_GENRES = ["rock", "pop", "hip-hop", "electronic", "jazz", "classical", "blues"]
    if genre not in VALID_GENRES:
        genre = "pop"

    score    = float(score)
    score    = max(0.0, min(score, 1.0))
    data     = data or {}

    mood_query        = score_to_mood(score, genre)
    pop_min, pop_max  = popularity_range(data)

    print(f"QUERY: {mood_query} | SCORE: {score:.2f} | POP: {pop_min}-{pop_max}")

    # =========================
    # ETAPA 1: artistas do gênero filtrados por popularidade
    # =========================
    try:
        artist_results = sp.search(
            q=f"genre:{genre}",
            type="artist",
            limit=10,       # pega mais para ter margem no filtro
            market="US"
        )
        artists = artist_results.get("artists", {}).get("items", [])

        # Filtra artistas pela mesma faixa de popularidade
        artists = [a for a in artists if pop_min <= a.get("popularity", 0) <= pop_max]

        artist_ids = [a["id"] for a in artists[:4]]

        if artist_ids:
            tracks = []
            for artist_id in artist_ids:
                top = sp.artist_top_tracks(artist_id, country="US")
                for t in top.get("tracks", [])[:3]:
                    tracks.append(t)

            # Aplica filtro de popularidade nas tracks também
            tracks = filter_by_popularity(tracks, pop_min, pop_max)

            # Ordena: score alto = mais popular primeiro, score baixo = menos popular primeiro
            tracks.sort(key=lambda t: t["popularity"], reverse=(score >= 0.5))

            if len(tracks) >= 3:
                return tracks[:10]

    except Exception as e:
        print("Erro na busca por artistas:", e)

    # =========================
    # FALLBACK: mood + gênero com filtro de popularidade
    # =========================
    try:
        results = sp.search(
            q=mood_query,
            type="track",
            limit=10,       # pega mais para ter margem no filtro
            market="US"
        )
        tracks = results.get("tracks", {}).get("items", [])
        tracks = filter_by_popularity(tracks, pop_min, pop_max)
        tracks.sort(key=lambda t: t["popularity"], reverse=(score >= 0.5))
        return tracks[:10]

    except Exception as e:
        print("Erro no fallback:", e)

    return []


def create_playlist(token, track_uris, score, genre):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    user_resp = requests.get("https://api.spotify.com/v1/me", headers=headers)
    user_resp.raise_for_status()

    payload = {
        "name": f"FuzzyMood — {genre.title()} ({round(score * 100)}%)",
        "public": True,
        "description": f"Playlist gerada pelo FuzzyMood. Score: {round(score, 3)}"
    }

    playlist_resp = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json=payload
    )
    playlist_resp.raise_for_status()
    playlist = playlist_resp.json()

    add_resp = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist['id']}/items",
        headers=headers,
        json={"uris": track_uris}
    )
    add_resp.raise_for_status()

    return playlist["external_urls"]["spotify"]
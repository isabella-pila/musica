from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .fuzzy import compute_fuzzy
from .spotify_service import (
    get_recommendations, create_playlist, build_sp,
)


from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings


# =========================
# OAuth — instância única
# =========================
def get_sp_oauth():
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="playlist-read-private playlist-modify-public playlist-modify-private",
        show_dialog=True
    )


# =========================
# Página inicial
# =========================
def index(request):
    return render(request, 'index.html')


# =========================
# Resultado
# =========================
def result_view(request):
    if request.method == 'POST':

        fuzzy_inputs = {
            'valence':      float(request.POST.get('valence')),
            'energy':       float(request.POST.get('energy')),
            'acousticness': float(request.POST.get('acousticness')),
        }

        genre = request.POST.get('genre')
        score = compute_fuzzy(fuzzy_inputs)

        tracks = get_recommendations(score, genre)

        request.session['tracks'] = [t['uri'] for t in tracks if t.get('uri')]
        request.session['score']  = score
        request.session['genre']  = genre

        defuzz_percentage = int(round(score * 100))
        if score <= 0.25: defuzz_category = "Calmo"
        elif score <= 0.45: defuzz_category = "Tranquilo"
        elif score <= 0.65: defuzz_category = "Moderado"
        elif score <= 0.85: defuzz_category = "Alegre"
        else: defuzz_category = "Agitado"

        v_level = "Alto" if fuzzy_inputs['valence'] >= 0.55 else "Baixo" if fuzzy_inputs['valence'] <= 0.45 else "Médio"
        e_level = "Alto" if fuzzy_inputs['energy'] >= 0.55 else "Baixo" if fuzzy_inputs['energy'] <= 0.45 else "Médio"
        a_level = "Alta" if fuzzy_inputs['acousticness'] >= 0.55 else "Baixa" if fuzzy_inputs['acousticness'] <= 0.45 else "Média"

        fuzzy_explanation = f"Como você combinou Felicidade de nível {v_level}, Energia num patamar {e_level} e densidade Acústica {a_level}, a lógica fuzzy ponderou as regras e resultou num estilo {defuzz_category} ({defuzz_percentage}%)."

        return render(request, 'result.html', {
            'tracks': tracks,
            'score':  round(score, 3),
            'defuzz_percentage': defuzz_percentage,
            'defuzz_category': defuzz_category,
            'fuzzy_explanation': fuzzy_explanation,
        })

    return redirect('index')


# =========================
# Login Spotify
# =========================
def spotify_login(request):
    request.session.pop('token_info', None)
    sp_oauth = get_sp_oauth()
    return redirect(sp_oauth.get_authorize_url())


# =========================
# Callback OAuth
# =========================
def callback(request):
    sp_oauth = get_sp_oauth()
    code = request.GET.get('code')

    if not code:
        return HttpResponse("Erro na autenticação.")

    token_info = sp_oauth.get_access_token(code, as_dict=True)
    print("TOKEN:", token_info)

    request.session['token_info'] = token_info

    track_uris = request.session.get('tracks', [])
    score      = request.session.get('score', 0.5)
    genre      = request.session.get('genre', 'pop')

    if not track_uris:
        return HttpResponse("Nenhuma música disponível. Volte e gere uma playlist primeiro.")

    try:
        playlist_url = create_playlist(
            token=token_info['access_token'],
            track_uris=track_uris,
            score=score,
            genre=genre
        )
        print("PLAYLIST URL:", playlist_url)
    except Exception as e:
        return HttpResponse(f"Erro ao criar playlist: {e}")

    return render(request, 'playlist_created.html', {
        'playlist_url': playlist_url
    })


# =========================
# Teste (pode remover depois)
# =========================
def teste_playlist(request):
    token_info = request.session.get('token_info')
    if not token_info:
        return JsonResponse({"erro": "Não autenticado. Acesse /login/ primeiro."})

    build_sp(token_info['access_token'])
    playlists = search_playlists("rock triste sad", limit=3)
    resultado = []
    for p in playlists:
        pid = p.get("id")
        tracks = get_tracks_from_playlist(pid)
        resultado.append({
            "playlist": p.get("name"),
            "id": pid,
            "tracks_count": len(tracks),
            "erro": "VAZIO" if not tracks else "OK",
            "primeira_musica": tracks[0].get("name") if tracks else None,
        })
    return JsonResponse({"playlists": resultado})
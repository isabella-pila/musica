from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .fuzzy import compute_fuzzy
from .spotify_service import get_recommendations, create_playlist, build_sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

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
        scope="playlist-read-public playlist-read-private playlist-modify-public playlist-modify-private",
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

        spotify_filters = {
            'popularity': float(request.POST.get('popularity', 50)),
            'nostalgia':  float(request.POST.get('nostalgia', 50)),
        }

        genre = request.POST.get('genre')
        score = compute_fuzzy(fuzzy_inputs)

        # Salva os dados do formulário na sessão ANTES de ir para o login
        request.session['pending_fuzzy']   = fuzzy_inputs
        request.session['pending_filters'] = spotify_filters
        request.session['pending_genre']   = genre
        request.session['pending_score']   = score

        # Se não tem token ainda, vai para o login do Spotify primeiro
        token_info = request.session.get('token_info')
        if not token_info:
            return redirect('spotify_login')

        # Renova o token se estiver expirado
        sp_oauth = get_sp_oauth()
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            request.session['token_info'] = token_info

        # Inicializa o Spotipy com o token do usuário
        build_sp(token_info['access_token'])

        tracks = get_recommendations(score, genre, spotify_filters)

        request.session['tracks'] = [t['uri'] for t in tracks if t.get('uri')]
        request.session['score']  = score
        request.session['genre']  = genre

        # Gráfico
        fig, ax = plt.subplots()
        ax.bar(['Score'], [score])
        ax.set_title('Score Fuzzy da Playlist')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        graph = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)

        return render(request, 'result.html', {
            'tracks': tracks,
            'graph':  graph,
            'score':  round(score, 3),
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

    # ✅ Inicializa o sp do spotify_service com o token do usuário
    build_sp(token_info['access_token'])

    # Se veio de um formulário pendente (primeiro login), gera as recomendações agora
    pending_score   = request.session.pop('pending_score', None)
    pending_genre   = request.session.pop('pending_genre', None)
    pending_filters = request.session.pop('pending_filters', {})

    if pending_score is not None:
        tracks = get_recommendations(pending_score, pending_genre, pending_filters)
        request.session['tracks'] = [t['uri'] for t in tracks if t.get('uri')]
        request.session['score']  = pending_score
        request.session['genre']  = pending_genre

        # Gráfico
        fig, ax = plt.subplots()
        ax.bar(['Score'], [pending_score])
        ax.set_title('Score Fuzzy da Playlist')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        graph = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)

        return render(request, 'result.html', {
            'tracks': tracks,
            'graph':  graph,
            'score':  round(pending_score, 3),
        })

    # Fluxo normal: criar playlist com tracks já salvos
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
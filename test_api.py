import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import json

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
))

# Test 1: Search tracks limit=10 - check all keys
print("=== TEST 1: Track keys ===")
try:
    r = sp.search(q='sertanejo', type='track', limit=3)
    tracks = r['tracks']['items']
    if tracks:
        t = tracks[0]
        print(f"Track keys: {list(t.keys())}")
        print(f"Name: {t.get('name')}")
        print(f"Artists: {t.get('artists', [{}])[0].get('name')}")
        print(f"Popularity: {t.get('popularity', 'N/A')}")
        print(f"ID: {t.get('id')}")
        print(f"URI: {t.get('uri')}")
        album = t.get('album', {})
        print(f"Album images: {len(album.get('images', []))}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Playlist items with encoding fix
print("\n=== TEST 2: Playlist items ===")
try:
    r = sp.search(q='sertanejo', type='playlist', limit=5)
    playlists = r['playlists']['items']
    print(f"Found {len(playlists)} playlists")
    
    for p in playlists:
        pid = p['id']
        try:
            items = sp.playlist_items(pid, additional_types=['track'], market='BR', limit=5)
            tracks = [i['track'] for i in items['items'] if i and i.get('track')]
            if tracks:
                print(f"SUCCESS! Playlist {pid}: {len(tracks)} tracks")
                for t in tracks:
                    name = t.get('name', '?')
                    artist = t.get('artists', [{}])[0].get('name', '?')
                    print(f"  - {name} / {artist}")
                break
            else:
                print(f"  Playlist {pid}: 0 tracks")
        except Exception as e2:
            err = str(e2)
            if '403' in err:
                print(f"  Playlist {pid}: 403 Forbidden")
            else:
                print(f"  Playlist {pid}: {err[:80]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Try sp.playlist() instead of sp.playlist_items()
print("\n=== TEST 3: sp.playlist() full endpoint ===")
try:
    r = sp.search(q='sertanejo hits', type='playlist', limit=5)
    playlists = r['playlists']['items']
    
    for p in playlists:
        pid = p['id']
        try:
            full = sp.playlist(pid, market='BR')
            tracks = full.get('tracks', {}).get('items', [])
            if tracks:
                print(f"SUCCESS with sp.playlist()! {len(tracks)} tracks")
                for item in tracks[:3]:
                    t = item.get('track', {})
                    if t:
                        name = t.get('name', '?')
                        artist = t.get('artists', [{}])[0].get('name', '?')
                        print(f"  - {name} / {artist}")
                break
            else:
                print(f"  Playlist {pid}: 0 tracks")
        except Exception as e2:
            err = str(e2)
            if '403' in err:
                print(f"  Playlist {pid}: 403")
            else:
                print(f"  Playlist {pid}: {err[:80]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 4: Check actual max limit for track search
print("\n=== TEST 4: Finding max limit ===")
for lim in [5, 10, 11, 15]:
    try:
        r = sp.search(q='pop', type='track', limit=lim)
        print(f"  limit={lim}: OK ({len(r['tracks']['items'])} results)")
    except Exception as e:
        print(f"  limit={lim}: FAILED ({str(e)[:50]})")

import os
import re
import json
import spotipy
import pafy
import shutil
from pydub import AudioSegment
from youtube_search import YoutubeSearch
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import YouTube

current_directory = os.getcwd()

cid = "c1f5b4e4627240bf8d10ee352d886fd1"
secret = "ded59152371e4590ae8954f1f4284809"
username = "bocozd7wqp0x70ttrgci5ojpc"
playlist_base_id = "20YjJd6QGy4nWTeZ0ifewt"

client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

playlist_dict = {}
playlists = sp.user_playlists(username)
for item in playlists["items"]:
    playlist_dict.update({item["name"]: item['id']})


while True:
    print("Here is a list of your playlists:")
    for item in playlist_dict.keys():
        print(item)
    input_playlist = input("Pick a playlist, or type \"manual\" to input a playlist ID: ")
    if input_playlist in str(playlist_dict.keys()):
        playlist_base_id = playlist_dict[input_playlist]
        break
    elif input_playlist.lower() == "manual":
        playlist_base_id = input("Please enter the playlist ID:\n")
        break
    else:
        print("\nPlease enter a valid playlist/")


print("Fetching list of songs")
song_list = []
playlist_id = 'spotify:user:spotifycharts:playlist:' + playlist_base_id
playlist_offset = 0
results = sp.playlist_tracks(playlist_base_id)
while len(results['items']) != 0:
    results = sp.playlist_tracks(playlist_base_id, offset = playlist_offset)
    for item in results['items']:
        song_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        full_song_name = str(artist_name) + " " + str(song_name)
        song_list.append(full_song_name)
    playlist_offset += 100
print("Finished fetching list of songs")

print("Generating list of urls")
url_list = []

for search_query in song_list:
  search_query = search_query.replace(" ", "+")
  results = YoutubeSearch(search_query, max_results = 1).to_dict()
  video_id = results[0]["id"]
  url_list.append("https://www.youtube.com/watch?v=" + video_id)
for i in url_list:
    print(i)
print("Generated list of urls")

new_dir = input_playlist 
try:
    os.mkdir(new_dir)
except:
    shutil.rmtree(new_dir, ignore_errors=True)
    os.mkdir(new_dir)

print("Downloading audio files (webm)")
new_full_dir = current_directory + "/" + new_dir

for url in url_list:
    result = pafy.new(url)
    best_quality_audio = result.getbestaudio(preftype = "webm")
    best_quality_audio.download(new_full_dir)
print("Finished downloading audio files (webm)")

print("Converting audio files to mp3")
index = 0
for file in os.listdir(new_full_dir):
  convert_dir = new_full_dir + "/" + str(file)
  webm_audio = AudioSegment.from_file(convert_dir, format="webm")
  webm_audio.export(new_full_dir + "/" + str(song_list[index]) + ".mp3", format = "mp3")
  index += 1
print("Finished converting audio files to mp3")

print("Deleting .webm files")
for item in os.listdir(new_full_dir):
  if item.endswith(".webm"):
    os.remove(os.path.join(new_full_dir, item))
print("Deleted .webm files")

print("Finished!")

import os
import re
import json
from sys import float_repr_style
import spotipy
import pafy
import shutil
from pydub import AudioSegment
from youtube_search import YoutubeSearch
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import YouTube

#gets current working directory 
current_directory = os.getcwd()

#prompt stuff
while True:
    response = input("Type \"manual\" to manually enter Spotify API credentials, or \"saved\" to read credentials from \"info.txt\"\n> ")
    if response.lower() == "manual":
        fhand = open("info.txt", "w")
        to_write = []
        cid = input("Enter your Client API ID: ")
        to_write.append(cid)
        secret = input("Enter your Client Secret ID: ")
        to_write.append(secret)
        username = input("Enter your username (the really long garbled one, not your display name): ")
        to_write.append(username)
        fhand.writelines(to_write)
        fhand.close()
        break
    elif response.lower() == "saved":
        try:
            fhand = open("info.txt", "r")
        except:
            print("No API info saved, please manually enter it.")
            continue
        lines = fhand.readlines()
        fhand.close()
        cid = lines[0].strip()
        secret = lines[1].strip()
        username = lines[2].strip()
        break
    else:
        print("Please enter either \"manual\" or \"saved.\"")

#connects to the spotify api or something
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


#stores the list of playlists with the ID of the playlist
playlist_dict = {}
playlists = sp.user_playlists(username)
for item in playlists["items"]:
    playlist_dict.update({item["name"]: item['id']})

#prompts either to choose a playlist found above or to manually input a playlist ID
while True:
    print("Here is a list of your playlists:\n")
    for item in playlist_dict.keys():
        print(item)
    input_playlist = input("\nPick a playlist, or type \"manual\" to input a playlist ID: ")
    if input_playlist in str(playlist_dict.keys()):
        playlist_base_id = playlist_dict[input_playlist]
        break
    elif input_playlist.lower() == "manual":
        playlist_base_id = input("Please enter the playlist ID:\n")
        break
    else:
        print("\nPlease enter a valid playlist/")

#creates a folder in Output with the playlist name
new_dir = input_playlist
try:
    os.mkdir(current_directory + "/Output/" + new_dir)
except:
    shutil.rmtree(current_directory + "/Output/" + new_dir, ignore_errors=True)
    os.mkdir(current_directory + "/Output/" + new_dir)

#gets the list of songs from the above playlist in [artist] [name] format
print("Fetching list of songs")
invalid_char = '<>:"/\|?*' #characters that can't be in file names
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
        #removes all invalid chars from song name 
        for char in invalid_char:
            full_song_name = full_song_name.replace(char, '')
        song_list.append(full_song_name)
    playlist_offset += 100
print("Finished fetching list of songs")



failed_songs = []
for song_name_org in song_list:
    id_list = []
    #print("\n\nGenerating list of video ids for " + song_name_org[0:45])
    song_name = song_name_org.replace(" ", "+")
    results = YoutubeSearch(song_name, max_results = 4).to_dict()
    for i in range(0, 4):
        video_id = results[i]["id"]
        id_list.append(video_id)
    #print("Generated list of ids for " + song_name_org[0:45])
    #converts the yt id to .webm file 
    filename = song_name_org[0:63] + ".webm"
    new_full_dir = current_directory + "/Output/" + new_dir + "/" + filename
    for index, id in enumerate(id_list):
        try:
            result = pafy.new(id, gdata = False)
        except:
            print("Fetch Failed, trying again with following search result")
            if index == 3:
                print("Couldn't download " + song_name)
                failed_songs.append(song_name_org)
                break
            continue
        #gets the best quality webm
        webm_audio = result.getbestaudio(preftype = "webm")
        #downloads to the the file path above
        print('Downloading ' + song_name_org[0:45])
        try:
            webm_audio.download(new_full_dir, quiet = True)
        except:
            print("Download Failed, trying again with following search result")
            if index == 3:
                print("Couldn't download " + song_name)
                failed_songs.append(song_name_org)
                break
            continue
        #print("breakpoint")
        break
            

#force appends .webm to the end of the filename just in case my code done goofed
new_full_dir = current_directory + "/Output/" + new_dir
for file in os.listdir(new_full_dir):
    if file.endswith(".webm") == False:
        current_dir = new_full_dir + "/" + file
        os.rename(current_dir, current_dir + ".webm")


print("Converting audio files to mp3")
new_full_dir = current_directory + "/Output/" + new_dir
index = 0
for file in os.listdir(new_full_dir):
    #print(str(song_list[index]) + " : " + file)
    convert_dir = new_full_dir + "/" + file
    webm_audio = AudioSegment.from_file(convert_dir, format="webm")
    webm_audio.export(new_full_dir + "/" + str(file)[0:-5] + ".mp3", format = "mp3")
    index += 1  
print("Finished converting audio files to mp3")


print("Deleting .webm files")
for item in os.listdir(new_full_dir):
  if item.endswith(".webm"):
    os.remove(os.path.join(new_full_dir, item))


print("Deleted .webm files")

print("Finished!")
print("Failed songs: " + str(len(failed_songs)))
for i in failed_songs:
    print(i)

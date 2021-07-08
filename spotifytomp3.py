import os
import time
from sys import float_repr_style # is this actually used? we may never know
import spotipy
import pafy
import shutil
from pydub import AudioSegment
from youtube_search import YoutubeSearch
from spotipy.oauth2 import SpotifyClientCredentials


#gets current working directory 
current_directory = os.getcwd()

#creates Output folder if it doesn't exist
try:
    os.mkdir(current_directory + "/Output/")
except:
    pass


#gets api info from the user
while True:
    response = input("Type \"manual\" to manually enter Spotify API credentials, or \"saved\" to read credentials from \"info.txt\"\n> ")
    if response.lower() == "manual":
        fhand = open("info.txt", "w")
        to_write = []
        cid = input("Enter your Client API ID: ")
        to_write.append(cid + "\n")
        secret = input("Enter your Client Secret ID: ")
        to_write.append(secret + "\n")
        #username = input("Enter your username (the really long garbled one, not your display name): ")
        #to_write.append(username + "\n")
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
        print("\nPlease enter either \"manual\" or \"saved.\"")

#connects to the spotify api or something
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

while True:
    response = input("\nType \"list\" to fetch a list of your playlists or type \"manual\" to input a Spotify playlist ID\n> ")
    if response.lower() == "manual":
        playlist_id = input("Please enter the playlist ID:\n")
        input_playlist = sp.playlist(playlist_id)["name"]
        break
    elif response.lower() == "list":
        while True:
            response = input("\nType \"read\" to read the username from \"info.txt\" or type \"input\" to manually input your username\n> ")
            if response.lower() == "read":
                fhand = open("info.txt", "r")
                lines = fhand.readlines()
                fhand.close()
                username = lines[2].strip()
                break
            elif response.lower() == "input":
                username = input("Enter your username (the really long garbled one, not your display name): ")
                to_write = username + "\n"
                fhand = open("info.txt", "a")
                fhand.write(to_write)
                fhand.close()
                break
            else:
                print("Please type either of the choices")
        playlists_dict = {}
        try:
            playlists = sp.user_playlists(username)
        except:
            print("Invalid username, cilent id, or cilent secret; please reinput Spotify credentials")
            quit()
        for item in playlists["items"]:
            playlists_dict.update({item["name"]: item['id']})
        while True:
            print("Here is a list of your playlists:\n")
            for item in playlists_dict.keys():
                print(item)
            input_playlist = input("\nPick a playlist: ")
            if input_playlist in str(playlists_dict.keys()):
                playlist_id = playlists_dict[input_playlist]
                break
            else:
                print("\nPlease enter a valid playlist/")
        break
    else:
        print("Please type either of the given options.\n")

#creates a folder in Output with the playlist_name = input_playlist
playlist_name = input_playlist
try:
    os.mkdir(current_directory + "/Output/" + playlist_name)
except:
    while True:
        response = input("This folder already exists. Would you like to keep existing files in the folder or do you want to overwrite them?\n(Y for keep, N for overwrite)\n> ")

        if response.lower() == 'y':
            break
        elif response.lower() == "n":
            shutil.rmtree(current_directory + "/Output/" + playlist_name, ignore_errors=True)
            os.mkdir(current_directory + "/Output/" + playlist_name)
            break
        else:
            print("Please enter Y or N\n")

#gets the list of songs from the above playlist in [artist] [name] format
print("Fetching list of songs")
invalid_char = '<>:"/\|?*' #characters that can't be in file names
song_list = []
playlist_offset = 0
results = sp.playlist_tracks(playlist_id)
while len(results['items']) != 0:
    results = sp.playlist_tracks(playlist_id, offset = playlist_offset)
    for item in results['items']:
        song_title = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        full_song_name = str(artist_name) + " - " + str(song_title)
        #removes all invalid chars from song name 
        for char in invalid_char:
            full_song_name = full_song_name.replace(char, '')
        song_list.append(full_song_name)
    playlist_offset += 100
print("Finished fetching list of songs")


playlist_dir = current_directory + "/Output/" + playlist_name
failed_songs = []
#goes through each song, downloads the yt video in webm form, converts to mp3
for song_name in song_list:

    #divider for aesthetics
    print("-------------------------------------")

    #just a bunch of variable names to make the code easier to read
    song_longform = song_name[0:63]
    song_shortform = song_name[0:45]
    song_webm = song_longform + ".webm"
    song_mp3 = song_longform + ".mp3"

    #says that the webm file exists, no action is needed as pafy will skip
    if os.path.exists(playlist_dir + "/" + song_webm):
        print(song_longform + "'s WEBM file already exists\n")
    #says that the mp3 file exists, skips the whole process
    if os.path.exists(playlist_dir + "/" + song_mp3):
        print(song_longform + "'s mp3 file already exists\n")
        continue
    id_list = []
    #generates ids for the first 4 results. why 4? no clue
    song_name = song_name.replace(" ", "+")
    results = YoutubeSearch(song_name, max_results = 4).to_dict()
    for i in range(0, 4):
        try:
            video_id = results[i]["id"]
        except:
            print('getting a video id failed')
        id_list.append(video_id)

    #converts the yt id to .webm file 
    for index, id in enumerate(id_list):
        #attempts to fetch video info, will try with first 4 yt results before eating shit
        try:
            result = pafy.new(id, gdata = False)
        except:
            print("\nFetch Failed, trying again in 5 seconds...\n")
            time.sleep(5)
            try:
                result = pafy.new(id, gdata = False)
            except:
                print("\nFetch Failed, trying again with following search result\n")
            if index == 3:
                print("Couldn't download " + song_shortform)
                failed_songs.append(song_name)
                break
            continue
        #gets the best quality webm
        webm_audio = result.getbestaudio(preftype = "webm")
        print('Downloading ' + song_shortform)
        #attempts downloads, will try with first 4 yt results before eating shit
        try:
            webm_audio.download(playlist_dir + "/" + song_webm, quiet = True)
        except:
            print("\nDownload Failed, trying again with following search result\n")
            if index == 3:
                print("Couldn't download " + song_shortform)
                failed_songs.append(song_name)
                break
            continue
        break
    #converts webm file to mp3
    print("Converting " + song_shortform + " webm file to mp3\n")
    webm_audio = AudioSegment.from_file(playlist_dir + "/" + song_webm, format="webm")
    webm_audio.export(playlist_dir + "/" + song_mp3, format = "mp3")
    index += 1  
    print("Converted " + song_shortform + " to mp3")

#deletes all the leftover .webm files
print("-------------------------------------")
print("Deleting .webm files\n")

for item in os.listdir(playlist_dir):
  if item.endswith(".webm"):
    os.remove(os.path.join(playlist_dir, item))

print("Deleted .webm files")

print("-------------------------------------")
print("Finished!")
print("Failed songs: " + str(len(failed_songs)))
for i in failed_songs:
    print(i)


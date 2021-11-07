import sys,requests,json,os
from os import path
from pytube import YouTube
from glob import iglob
from moviepy.editor import *
import eyed3
from apiclient.discovery import build

import json

from pprint import pprint as pp


SP_CLIENT_ID = "3b331be031c14662a6c147c5cf4a6a8b" #replace with your spotify client id
SP_CLIENT_SECRET = "2b3200cd3ef9407c8506e8a9d78ad2b7" #replace with your spotify secret

AUTH_URL = 'https://accounts.spotify.com/api/token'


desired_bitrate = '320k'

auth_response = requests.post(AUTH_URL,{
    'grant_type' : 'client_credentials',
    'client_id' : SP_CLIENT_ID,
    'client_secret' : SP_CLIENT_SECRET}
)

auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']

headers = {
    'Authorization' : 'Bearer {token}'.format(token=access_token)
}


def download_album(album_name):
    prev_dir = os.getcwd()
    os.chdir(r"music") #replace with your music directory
    if path.exists(album_name):
        print("Album already downloaded!")
        return
    os.mkdir(album_name)
    os.chdir(album_name)
    if path.exists('art.png'):
        os.remove('art.png')

    Sp_BASE_URL = 'https://api.spotify.com/v1/'
    album_name_api_req = album_name.replace(" ","%20")
    query1 = 'search?q=album:'+album_name_api_req+'&type=album'
    spotify_a1 = requests.get(Sp_BASE_URL+query1,headers=headers)
    spotify_a2 = spotify_a1.json()
    try:
        album_id = spotify_a2['albums']['items'][0]['id']
    except IndexError:
        print("Album not found on Spotify")
        return
    query2 = 'albums/'+album_id
    spotify_b1 = requests.get(Sp_BASE_URL+query2,headers=headers)
    spotify_b2 = spotify_b1.json()

    track_list = []
    no_of_tracks = int(spotify_b2['total_tracks'])
    print("Track list : ")
    for i in range(no_of_tracks):
        track_list.append(spotify_b2['tracks']['items'][i]['name'])
        print(f"{i+1}) "+track_list[i])

    print("\nEnter track numbers to download (separate by comma(,)) or press Enter to download all songs or no to search again")
    print("-->> ",end='')
    requested_str = str(input())
    requested_tracks_index = []
    if requested_str=='no':
        return
    elif requested_str=='':
        for i in range(no_of_tracks):
            requested_tracks_index.append(i)
    else:
        for i in range(0,len(requested_str)+1,2):
            requested_tracks_index.append(int(requested_str[i])-1)

    requested_tracks_ids = []
    requested_tracks = []
    requested_tracks_artists = []
    for i in range(len(requested_tracks_index)):
        requested_tracks_ids.append(spotify_b2['tracks']['items'][requested_tracks_index[i]]['id'])
        requested_tracks.append(spotify_b2['tracks']['items'][requested_tracks_index[i]]['name'])
        requested_tracks_artists.append(spotify_b2['tracks']['items'][requested_tracks_index[i]]['artists'][0]['name'])
        
    
    album_name = spotify_b2['name'].replace(' (Original Motion Picture Soundtrack)','') if ' (Original Motion Picture Soundtrack)' in spotify_b2['name'] else spotify_b2['name']

    #ALBUM ART DOWNLOAD
    r = requests.get(spotify_b2['images'][1]['url'])
    with open("art.png",'wb') as f:
        f.write(r.content)

    # SONG.LINK API SEGMENT
    YT_LINKS = []
    remove = []
    for i in range(len(requested_tracks_index)):
        print("Downloading Metadata for song number: ", i + 1)
        songlink_response = requests.get('https://api.song.link/v1-alpha.1/links?url=spotify%3Atrack%3A'+requested_tracks_ids[i]+'&userCountry=IN')
        links_json = songlink_response.json()
        try:
            YT_LINKS.append(links_json['linksByPlatform']['youtube']['url'])
        except KeyError:
            print(f"{requested_tracks[i]} is not found on API database")
            print("Search on youtube(y) or skip(n) : ",end='')
            choice = input()
            if choice=='y':
                YT_DEVELOPER_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  #replace with your YouTube developer key
                YOUTUBE_API_SERVICE_NAME = "youtube"
                YOUTUBE_API_VERSION = "v3"
                youtube_object = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey = YT_DEVELOPER_KEY)
                def youtube_search_keyword(query, max_results):
                    search_keyword = youtube_object.search().list(q = query, part = "id, snippet",
                                                               maxResults = max_results).execute()
                    results = search_keyword.get("items", [])
                    return results
                results = youtube_search_keyword(requested_tracks[i]+' '+album_name+' movie audio song',1)
                video_id = results[0]['id']['videoId']
                YT_BASE_URL = 'https://www.youtube.com/watch?v='
                YT_LINKS.append(YT_BASE_URL+video_id)
            else:
                print(f"Skipping {requested_tracks[i]}")
                remove.append(i)
    k=0
    for i in range(len(remove)):
        requested_tracks_index.pop(remove[i]+k)
        requested_tracks.pop(remove[i]+k)
        requested_tracks_artists.pop(remove[i]+k)
        k-=1

    # DOWNLOAD,RENAME,CONVERT,ADD METADATA
    print('')
    video_objs = []

    # list of songs that failed to download
    failed_songs = []
    # iterate and download each song
    for i in range(len(requested_tracks_index)):
        #DOWNLOAD
        video_objs.append(YouTube(YT_LINKS[i]))
        print(f"Downloading {i+1}/{len(requested_tracks_index)} - {requested_tracks[i]} ",end='')
        try:
            video_objs[i].streams.get_audio_only().download()
            print(" -> Downloaded")
            #RENAME
            files = sorted(iglob(os.path.join(os.getcwd(),'*')),key=os.path.getctime,reverse=True)
            old_title = files[0].replace(os.getcwd()+'/','')
            new_title = requested_tracks[i]+ f' [{album_name}]'
            if '"' in new_title :
                new_title = new_title.replace('"','')
            if "'" in new_title :
                new_title = new_title.replace("'",'')
            if "\\" in new_title :
                new_title = new_title.replace("\\",'')
            if "/" in new_title :
                new_title = new_title.replace("/",'')
            os.rename(old_title,new_title+'.mp4')
            #CONVERT
            print("   [*] Converting to mp3")
            # convert using moviepy to mp3
            mp4_file = os.getcwd()+'\\'+new_title+'.mp4'
            mp3_file = os.getcwd()+'\\'+new_title+'.mp3'
            audioclip = AudioFileClip(mp4_file)#
            audioclip.write_audiofile(mp3_file, bitrate=desired_bitrate)
            audioclip.close()

            os.remove(os.getcwd()+'\\'+new_title+'.mp4')
            #ADD METADATA
            print("   [*] Adding metadata")
            mp3 = eyed3.load(os.getcwd()+'\\'+new_title+'.mp3')
            if (mp3.tag == None):
                mp3.initTag()
            mp3.tag.title = requested_tracks[i]
            mp3.tag.album = album_name
            mp3.tag.artist = requested_tracks_artists[i]
            mp3.tag.images.set(3, open("art.png", 'rb').read(), 'image/png')
            mp3.tag.save(version=eyed3.id3.ID3_V2_3)
        except Exception as e:
            print("Failed to download: ", requested_tracks[i])
            failed_songs.append(requested_tracks[i])

    os.remove("art.png")
    if len(video_objs)==len(requested_tracks_index):
        print("\nSuccessfully downloaded all songs")
    else:
        print("Something wrong\n")
        print("Failed to download the following songs: ", failed_songs)
        sys.exit()






def download_song(song_name):
    prev_dir = os.getcwd()
    os.chdir(r"music/songs") #replace with your music directory
    if path.exists(song_name+'-art.png'):
        os.remove(song_name+'-art.png')

    Sp_BASE_URL = 'https://api.spotify.com/v1/'
    song_name_api_req = song_name.replace(" ","%20")
    query1 = 'search?q='+song_name_api_req+'&type=track'
    spotify_a1 = requests.get(Sp_BASE_URL+query1,headers=headers)
    spotify_a2 = spotify_a1.json()
    # print out the first 30 songs to select from
    found_songs = spotify_a2['tracks']['items'][:30] 
    for idx, x in enumerate(found_songs):
        idx+=1
        artist_name = x["artists"][0]["name"]
        song_name = x["name"]
        print(f"{idx}) {song_name} - {artist_name}")

    selected_song_number = int(input("\nWhich song would you like to download (1-30)?: "))
    selected_song = found_songs[selected_song_number-1]
    print("\n\n\n\n")

    album_name = selected_song["album"]["name"]
    #pp(selected_song)
    #return


    #ALBUM ART DOWNLOAD
    r = requests.get(selected_song["album"]["images"][0]["url"])
    with open(song_name+"-art.png",'wb') as f:
        f.write(r.content)

    # SONG.LINK API SEGMENT
    YT_LINKS = []
    remove = []
    print("Downloading Metadata")
    songlink_response = requests.get('https://api.song.link/v1-alpha.1/links?url=spotify%3Atrack%3A'+selected_song["id"]+'&userCountry=US')#####
    links_json = songlink_response.json()
    try:
        YT_LINKS.append(links_json['linksByPlatform']['youtube']['url'])
    except KeyError:
        print(f"{requested_tracks[i]} is not found on API database")
        print("Search on youtube(y) or skip(n) : ",end='')
        choice = input()
        if choice=='y':
            YT_DEVELOPER_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  #replace with your YouTube developer key
            YOUTUBE_API_SERVICE_NAME = "youtube"
            YOUTUBE_API_VERSION = "v3"
            youtube_object = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey = YT_DEVELOPER_KEY)
            def youtube_search_keyword(query, max_results):
                search_keyword = youtube_object.search().list(q = query, part = "id, snippet",
                                                            maxResults = max_results).execute()
                results = search_keyword.get("items", [])
                return results
            results = youtube_search_keyword(requested_tracks[i]+' '+album_name+' movie audio song',1)
            video_id = results[0]['id']['videoId']
            YT_BASE_URL = 'https://www.youtube.com/watch?v='
            YT_LINKS.append(YT_BASE_URL+video_id)
        else:
            print(f"Skipping {requested_tracks[i]}")
            remove.append(i)
    k=0
    for i in range(len(remove)):
        requested_tracks_index.pop(remove[i]+k)
        requested_tracks.pop(remove[i]+k)
        requested_tracks_artists.pop(remove[i]+k)
        k-=1

    # DOWNLOAD,RENAME,CONVERT,ADD METADATA
    print('')
    video_objs = []

    # iterate and download each song
    #DOWNLOAD
    video_objs.append(YouTube(YT_LINKS[0]))    
    video_objs[0].streams.get_audio_only().download()
    print(" -> Downloaded")
    #RENAME
    files = sorted(iglob(os.path.join(os.getcwd(),'*')),key=os.path.getctime,reverse=True)
    old_title = files[0].replace(os.getcwd()+'/','')
    new_title = selected_song["name"] + f' [{album_name}]'
    if '"' in new_title :
        new_title = new_title.replace('"','')
    if "'" in new_title :
        new_title = new_title.replace("'",'')
    if "\\" in new_title :
        new_title = new_title.replace("\\",'')
    if "/" in new_title :
        new_title = new_title.replace("/",'')
    os.rename(old_title,new_title+'.mp4')
    #CONVERT
    print("   [*] Converting to mp3")
    # convert using moviepy to mp3
    mp4_file = os.getcwd()+'\\'+new_title+'.mp4'
    mp3_file = os.getcwd()+'\\'+new_title+'.mp3'
    audioclip = AudioFileClip(mp4_file)#
    audioclip.write_audiofile(mp3_file, bitrate=desired_bitrate)
    audioclip.close()

    os.remove(os.getcwd()+'\\'+new_title+'.mp4')
    #ADD METADATA
    print("   [*] Adding metadata")
    mp3 = eyed3.load(os.getcwd()+'\\'+new_title+'.mp3')
    if (mp3.tag == None):
        mp3.initTag()
    mp3.tag.title = selected_song["name"]
    mp3.tag.album = album_name


    # add artist metadata 
    # must use a loop to include features
    contributing_artists = ""
    for x in selected_song["artists"]:
        if contributing_artists != "":
            contributing_artists += ("/" + x["name"])
        else:
            contributing_artists += x["name"]
    print('"' + contributing_artists + '"')
    # add other metadata
    mp3.tag.artist = contributing_artists
    mp3.tag.images.set(3, open(song_name+"-art.png", 'rb').read(), 'image/png')
    mp3.tag.save(version=eyed3.id3.ID3_V2_3)

    os.remove(song_name+"-art.png")
    print("Successfully the song")



def download_playlist(playlist_url):
    prev_dir = os.getcwd()
    os.chdir(r"music/playlists") #replace with your music directory

    Sp_BASE_URL = 'https://api.spotify.com/v1/'
    playlist_api_req = playlist_url
    query1 = 'playlists/'+playlist_api_req
    spotify_a1 = requests.get(Sp_BASE_URL+query1,headers=headers)
    spotify_a2 = spotify_a1.json()

    # create new folder for playlist
    playlist_name = spotify_a2["name"]
    if os.path.isdir(playlist_name):
        print("Playlist with the same name already downloaded.")
        return
    os.makedirs(playlist_name)
    os.chdir(playlist_name)

    # iterate tracks in playlist
    playlist_length = str(len(spotify_a2["tracks"]["items"]))
    failed_songs = []
    for idx, song in enumerate(spotify_a2["tracks"]["items"]):
        idxx = str(idx + 1)
        
        print(f"Downloading song: {idxx} / {playlist_length}")
        # extract metadata for that track
        song_data = song["track"]
        song_name = song_data["name"]
        song_album = song_data["album"]["name"]
        song_album_cover = song_data["album"]["images"][0]["url"]
        song_id = song_data["id"]
        song_artists = ""
        for idx2, artist in enumerate(song_data["artists"]):
            if idx2 == 0:
                song_artists += artist["name"]
            else:
                song_artists += ("/" + artist["name"])
        
        song_metadata = {
            "name": song_name,
            "album": song_album,
            "albumCover": song_album_cover,
            "artists": song_artists,
            "id": song_id
        }

        try:
            # get youtube link for the song
            # SONG.LINK API SEGMENT
            YT_LINKS = []
            remove = []
            songlink_response = requests.get('https://api.song.link/v1-alpha.1/links?url=spotify%3Atrack%3A'+song_metadata["id"]+'&userCountry=US')#####
            links_json = songlink_response.json()
            try:
                YT_LINKS.append(links_json['linksByPlatform']['youtube']['url'])
            except KeyError:
                print(f"{requested_tracks[i]} is not found on API database")
                print(f"Skipping {requested_tracks[i]}")
                remove.append(i)
            k=0
            for i in range(len(remove)):
                requested_tracks_index.pop(remove[i]+k)
                requested_tracks.pop(remove[i]+k)
                requested_tracks_artists.pop(remove[i]+k)
                k-=1



            # download song
            video_objs = []

            # iterate and download each song
            #DOWNLOAD
            video_objs.append(YouTube(YT_LINKS[0]))    
            video_objs[0].streams.get_audio_only().download()
            #RENAME
            files = sorted(iglob(os.path.join(os.getcwd(),'*')),key=os.path.getctime,reverse=True)
            old_title = files[0].replace(os.getcwd()+'/','')
            new_title = song_metadata["name"] + f' [{song_metadata["album"]}]'
            if '"' in new_title :
                new_title = new_title.replace('"','')
            if "'" in new_title :
                new_title = new_title.replace("'",'')
            if "\\" in new_title :
                new_title = new_title.replace("\\",'')
            if "/" in new_title :
                new_title = new_title.replace("/",'')
            os.rename(old_title,new_title+'.mp4')
            #CONVERT
            # convert using moviepy to mp3
            mp4_file = os.getcwd()+'\\'+new_title+'.mp4'
            mp3_file = os.getcwd()+'\\'+new_title+'.mp3'
            audioclip = AudioFileClip(mp4_file)#
            audioclip.write_audiofile(mp3_file, bitrate=desired_bitrate)
            audioclip.close()

            os.remove(os.getcwd()+'\\'+new_title+'.mp4')


            # download album art
            r = requests.get(song_metadata["albumCover"])
            with open(song_metadata["name"]+"-art.png",'wb') as f:
                f.write(r.content)

            # write metadata
            
            mp3 = eyed3.load(os.getcwd()+'\\'+new_title+'.mp3')
            if (mp3.tag == None):
                mp3.initTag()
            mp3.tag.title = song_metadata["name"]
            mp3.tag.album = song_metadata["album"]
            mp3.tag.artist = song_metadata["artists"]
            mp3.tag.images.set(3, open(song_metadata["name"]+"-art.png", 'rb').read(), 'image/png')
            mp3.tag.save(version=eyed3.id3.ID3_V2_3)

            os.remove(song_metadata["name"]+"-art.png")
        except Exception as e:
            failed_songs.append(song_metadata["name"])
    if len(failed_songs) > 0:
        print("\nFailed to download the following songs: ")
        for x in failed_songs:
            print(x)
        print("")














# starting loop
album_or_song = input("Do you want to download a song (1), album (2), or playlist (3)?: ")
if (album_or_song.startswith("2")):
    print("Enter album name ('z' to stop) : ",end='')
    album_name=str(input())
    if album_name!='z':
        download_album(album_name)
    else:
        sys.exit()
elif album_or_song.startswith("3"):
    print("Enter a playlist id ('z' to stop) : ", end='')
    playlist_id = str(input())
    if playlist_id != 'z':
        download_playlist(playlist_id)
    else:
        sys.exit()
elif (album_or_song.startswith("1")):
    print("Enter a song name ('z' to stop) : ", end='')
    song_name = str(input())
    if song_name != 'z':
        download_song(song_name)
    else:
        sys.exit()
    
#Completed

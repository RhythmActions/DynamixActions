import requests
import UnityPy
from http.cookies import SimpleCookie
from typing import Awaitable
import json
import os
import PIL
from PIL import Image
import datetime 
from datetime import datetime
from datetime import timezone
from datetime import timedelta

class DynamixServer:
    AppStore = "https://itunes.apple.com/lookup?id=945955095"

    def __init__(self):
        self.versionCode = self.get_version_code()
        self.newVersionCode = self.format_version_code(self.versionCode)
        serverlist = self.get_server_list()
        self.c4idURL = serverlist["c4id"]
        self.dynamixURL = serverlist["dynamix"]
        self.bundleURL = serverlist["bundle"]["iOS"]
        self.bundleList = self.get_bundle_list(serverlist["bundleList"]["iOS"])
        self.songlist = self.bundleURL + self.bundleList["version"] + "/iOS/_songlist"
        self.bundleURL = self.bundleURL + self.bundleList["version"] + "/iOS/"
        
    def get_version_code(self):
        return requests.get(self.AppStore).json()["results"][0]["version"]

    def format_version_code(self, versionCode):
        return ''.join([i.zfill(2) for i in versionCode.split('.')])

    def get_server_list(self):
        return requests.get(f"http://asset.dynamix.c4-cat.com/AssetBundles/server_list{self.newVersionCode}.json").json()

    def get_bundle_list(self, url):
        return requests.get(url).json()
    
    def download_bundle(self, url):
        import requests
        from io import BytesIO
        rawbundle = requests.get(url, stream=True).content
        return BytesIO(rawbundle)
    
    def get_songlist(self):
        bundle = self.download_bundle(self.songlist)
        asset = UnityPy.load(bundle)
        for obj in asset.objects:
            tree = obj.read_typetree()
            if(tree["m_Name"] == "SongList"):
                obj.save_typetree(tree)
                return tree


# 在事件循环中运行main函数
if __name__ == "__main__":
    server = DynamixServer()
    
    songlist_origin = server.get_songlist()['m_list']
    songlist = {"id": [], "Songs": {}}
    for song in songlist_origin["Songs"]:
        if("wavetest" in song["id"]):
            continue
        trueid = song["id"].split("_song_")[1]
        songlist["id"].append(trueid)
        newsong = {
            "id": song["id"],
            "Name": song["Name"],
            "BPM": song["BPM"],
            "Genre": song["Genre"],
            "Author": song["Author"],
            "PreviewAudio": song["PreviewAudio"]["id"],
            "Cover": song["Cover"]["id"],
            "Maps": song["Maps"]
        }
        songlist["Songs"][trueid] = newsong
    
    t = datetime.utcnow().replace(tzinfo=timezone.utc)
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    beijing_now = t.astimezone(SHA_TZ)
    beijing_now = beijing_now.strftime("%Y-%m-%d %H:%M:%S") 
    
    songlist['ver'] = server.versionCode
    songlist['updateTime'] = beijing_now
    with open("songlist.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(songlist, ensure_ascii=False, indent=4))
    # with open("songlist.json", "r", encoding="utf-8") as f:
    #     songlist = json.loads(f.read())
    for songid in songlist["id"]:
        song = songlist["Songs"][songid]
        songurl = server.bundleURL + song["id"].lower()
        coverurl = server.bundleURL + song["Cover"].lower()
        mapsurl = [server.bundleURL + map["id"].lower() for map in song["Maps"]]
        
        if(os.path.exists(os.path.join("Songs", songid))):
            print(f"Song {songid} already exists")
            continue
        os.makedirs(os.path.join("Songs", songid), exist_ok = True)    
        
        coverbundle = server.download_bundle(coverurl)
        asset = UnityPy.load(coverbundle)
        for obj in asset.objects:
            tree = obj.read_typetree()
            if(obj.type.name == "Sprite"):
                data = obj.read()
                img = data.image
                # img.save("cover/"+song["Cover"]+".png")
                img.save(os.path.join(f"Songs/{songid}", song["Cover"]+".png"))
                print(song["Cover"])
                break      
        for mapurl in mapsurl:
            mapbundle = server.download_bundle(mapurl)
            asset = UnityPy.load(mapbundle)
            for obj in asset.objects:
                tree = obj.read_typetree()
                if("m_mapID" not in tree.keys()):
                    continue              
                if(obj.type.name == "MonoBehaviour" and tree["m_mapID"].lower() in mapurl.lower()):
                    obj.save_typetree(tree)
                    with open(os.path.join(f"Songs/{songid}", tree["m_mapID"]+".json"), "w", encoding="utf-8") as f:
                        f.write(json.dumps(tree, ensure_ascii=False, indent=4))      
                    print(tree["m_mapID"])
    
        # break
    # bundle = server.download_bundle("https://cdn-al.c4-cat.com/Dynamix/AssetBundles/03180008/iOS/_song_restrictedaccess")
    # asset = UnityPy.load(bundle)
    # for obj in asset.objects:
    #     tree = obj.read_typetree()
    #     if(obj.type.name == "AudioClip"):
    #         print(obj.read_typetree()["m_Name"])
    #     print(tree["m_Name"])
    exit()
        # if(tree["m_Name"] == "SongList"):
        #     obj.save_typetree(tree)
        #     songlist = tree
        #     break
    
    with open("songlist.json", "r", encoding="utf-8") as f:
        songlist = json.loads(f.read())
    for songid in songlist["id"]:
        song = songlist["Songs"][songid]
        songurl = server.bundleURL + song["id"].lower()
        coverurl = server.bundleURL + song["Cover"].lower()
        mapsurl = [server.bundleURL + map["id"].lower() for map in song["Maps"]]
        
        print(songurl, coverurl, mapsurl)
            
            
    # with open("songlist.json", "w", encoding="utf-8") as f:
    #     f.write(json.dumps(songlist, ensure_ascii=False, indent=4))

    
    # bundle = server.download_bundle(server.songlist)
    # asset = UnityPy.load(bundle)
    # songlist: dict = {}
    # for obj in asset.objects:
    #     raw = obj.get_raw_data()
    #     tree = obj.read_typetree()
    #     if(tree["m_Name"] == "SongList"):
    #         obj.save_typetree(tree)
    #         songlist = tree
    #         break
    
    # print(json.dumps(tree, ensure_ascii = False, indent = 4))


    # print(json.dumps(server.__dict__, indent=4, ensure_ascii=False))
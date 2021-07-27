#!/usr/env python3


# Note Bin - throw files in a folder and forget about it. We take Notes of it... any time soon :D
#
#
# todo
#--------
#- data handler
#- data format like turtl?
#- package and structure with package imports etc
#- tagging implementation soon
#- rather json db, mongo?
#
#
#### hostbusters.dev ##### call at #####

# import time module, Observer, FileSystemEventHandler
import time, re, magic, spacy, sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pycld2 as cld2


# db
conn = sqlite3.connect('notebin.db', check_same_thread=False)

# todo from db
supportedLangs = {"GERMAN": "de_DE","de_DE": "de_core_news_sm",}


 
# thx: https://www.geeksforgeeks.org/create-a-watchdog-in-python-to-look-for-filesystem-changes/ 
path = "./throwbin"  
class OnMyWatch:
    # Set the directory on watch
    watchDirectory = path
  
    def __init__(self):
        self.observer = Observer()
  
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive = True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")
  
        self.observer.join()
  
  
class Handler(FileSystemEventHandler):
  
    @staticmethod
    def on_any_event(event):

        #if event.is_directory:
            #return None
        #print("Watchdog received "+event.event_type+" event - % s." % event.src_path)
        #elif event.event_type == 'created':
            # Event is created, you can process it now
        #    print("Watchdog received lame why created event - % s." % event.src_path)
        #elif event.event_type == 'modified':
            # Event is modified, you can process it now
        #    print("Watchdog received lame why modified event - % s." % event.src_path)
        if event.event_type == 'created':
            # Event is created, you can process it now
        #    print("Watchdog received lame why created event - % s." % event.src_path)
            if not event.is_directory: 
                f = event.src_path
                timenow = int(time.time())
                
                #newFile = open(f, "rb+")
                ma = magic.from_buffer(open(f, "rb").read(2048))
                m = magic.from_file(f, mime=True)
                query = [int(timenow), str(f), str(m)]
                queryMime = str(m)
                #print(str(query))
                #conn.executemany("INSERT OR REPLACE INTO fileIndex (timeNow, fileName, mime) VALUES (?, (?), ?);", [query])
                try:
                    checkMime = conn.execute("SELECT mimeID FROM mimeTypes WHERE mimeName = (?);", (queryMime,)) ###new table structure api_data: time(p) data jsonurl
                except:
                    conn.executemany("INSERT INTO mimeTypes (mimeName) VALUES (?);", [queryMime])
                    checkMime = conn.execute("SELECT mimeID FROM mimeTypes WHERE mimeName = (?);", [queryMime])
                
                conn.executemany("INSERT OR REPLACE INTO fileIndex (timeNow, fileName, fileMime) VALUES (?, (?),?);", [query])
                dbEntry = conn.execute("SELECT fileName FROM fileIndex WHERE fileID = ( select max(fileID) from fileIndex );")
                print(dbEntry)
                conn.commit()
                if m in ("application/json", "text/plain"): # reads mime
                    print("Detected %s encoding for reading index", m)
                    method = open
                    print(method, "file from", f)

                    isLang, textBytesFound, detailsLang = cld2.detect(open(f, "r+").read())
                    print(isLang,detailsLang[0][0])
                    try:
                        detectedLang = supportedLangs[detailsLang[0][0]]
                    except:
                        detectedLang = "NONE"
                    # True
                    #details[0]
                    # ('RUSSIAN', 'ru', 98, 404.0)

                    if isLang is True:
                        if detectedLang in supportedLangs:
                            
                            nlp = spacy.load(supportedLangs[detectedLang]) # spacy load detected lang file 
                            doc = nlp(open(f, "r+").read()) #sends file to nlp engine

                            for token in doc:
                                print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
                                        token.shape_, token.is_alpha, token.is_stop)
                            return(method)
                        else:
                            print("not a yet supported language (",supportedLangs.keys(),")")
                    else:
                        print("not a language, or something")
                elif m in ("application/gzip", "application/x-gzip"):
                    echo("Detected gzip encoding for reading index")
                    method = gzip.open
                    print(method, "file from", f)

                    return(method, f)

                else:
                    raise ValueError("Index is of unknown type: %s", m)

            else:
                folderNew = re.sub("[^\w]", " ",  event.src_path).split()
                folders = []
                folders.append(folderNew)
                print(folders)



    #file = open(file_name, "wb+") 
    #content = strip_tags(file.read())

  
if __name__ == '__main__':
    watch = OnMyWatch()
    watch.run()

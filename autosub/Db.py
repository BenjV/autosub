# Autosub Db.py
#
# The Autosub DB module
# 

# Database structure downloaded
# 0 id
# 1 show
# 2 season
# 3 episode
# 4 source
# 5 distro
# 6 releasegrp
# 7 quality
# 8 codec
# 9 website
# 10 language
# 11 timestamp
# 12 title
# 13 location

import os
import sqlite3
import logging
import autosub
import autosub.version as version

# Settings
log = logging.getLogger('thelogger')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class idCache():
    def __init__(self, DbConnect):
        self.query_getId    = "SELECT imdb_id, a7_id, tvdb_id, tvdb_name FROM show_id_cache WHERE show_name = ?"
        self.query_getInfo  = "SELECT a7_id, tvdb_id,tvdb_name FROM show_id_cache WHERE imdb_id = ?"
        self.query_checkId  = "SELECT * FROM show_id_cache WHERE show_name = ?"
        self.query_updateId = "UPDATE show_id_cache SET imdb_id =?, a7_id = ?, tvdb_id = ?, tvdb_name =? WHERE show_name = ?"
        self.query_setId    = "INSERT INTO show_id_cache (show_name, imdb_id, a7_id, tvdb_id, tvdb_name) VALUES (?,?,?,?,?)"
        self.connection     = DbConnect
        self.cursor         = DbConnect.cursor()

    def getId(self, ShowName):
        Name = ShowName.upper()
        try:
            Result = self.cursor.execute(self.query_getId, [Name]).fetchone()
            if Result:
                AddicId = int(Result[1]) if Result[1] else None
                return Result[0],AddicId,Result[2], Result[3]
            else:
                return None, None, None, ShowName
        except Exception as error:
            log.error(error.message)
            return None, None, None, ShowName

    def getInfo(self, ImdbId):
        try:
            Result = self.cursor.execute(self.query_getInfo, [ImdbId]).fetchone()
            if Result:
                AddicId = int(Result[0]) if Result[0] else None
                return AddicId, Result[1], Result[2]
            else:
                return None, None, None
        except Exception as error:
            log.error(error.message)
            return None, None, None

    def setId(self, ShowName, ImdbId, AddicId, TvdbId):
        Name = ShowName.upper()
        try:
            Result = self.cursor.execute(self.query_checkId,[Name]).fetchone()
            if Result:
                self.cursor.execute(self.query_updateId,[ImdbId, AddicId, TvdbId, ShowName, Name])
            else:
                self.cursor.execute(self.query_setId,[Name, ImdbId, AddicId, TvdbId, ShowName])
            self.connection.commit()
        except Exception as error:
            log.error(error.message)
        return

class downloads():
    def __init__(self,DbConnect):
        #self.query_flush = "delete from downloaded"
        self.query_get_filespecs = "SELECT location FROM  downloaded WHERE id = ?"
        self.query_add = "INSERT INTO downloaded (show,season,episode,timestamp,source,distro,releasegrp,quality,codec,website,language,title,location) values (?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.connection = DbConnect
        self.cursor = DbConnect.cursor()

    def getfilespecs(self, RowId):
        try:
            FileSpec = self.cursor.execute(self.query_get_filespecs, [RowId]).fetchone()[0]
        except Exception as error:
            log.error(error.message)
            FileSpec = None
        return FileSpec

    def addDown(self,data):
        try:
            self.cursor.execute(self.query_add,data)
            RowId = self.cursor.lastrowid
            self.connection.commit()
        except Exception as error:
            log.error(error.message)
            return 0
        return RowId

def createDatabase():
    #create the database

    try:     
        Db = sqlite3.connect(autosub.DBFILE)
        cursor=Db.cursor() 
        cursor.execute("CREATE TABLE show_id_cache (show_name TEXT UNIQUE PRIMARY KEY, imdb_id TEXT, a7_id TEXT, tvdb_id TEXT, tvdb_name TEXT)")
        cursor.execute("CREATE TABLE downloaded (id INTEGER PRIMARY KEY,show TEXT, season TEXT, episode TEXT,quality TEXT,distro TEXT,source TEXT,codec TEXT,releasegrp TEXT,website TEXT,language TEXT,timestamp DATETIME,title TEXT, location TEXT)")
        cursor.execute("CREATE TABLE sub_info (id INTEGER PRIMARY KEY, website TEXT,destination TEXT)")
        cursor.execute("PRAGMA user_version = 11")
        Db.commit()
        autosub.DBVERSION = 11
    except Exception as error:
        print error.message
        os._exit(1)
    Db.close()
    return True

def upgradeDb(from_version, to_version):
    upgrades = to_version - from_version
    if upgrades != 1:
        for x in range (0, upgrades):
            upgradeDb(from_version + x, from_version + x + 1)
    else:
        Db = sqlite3.connect(autosub.DBFILE)
        cursor = Db.cursor()
        if from_version == 1 and to_version == 2:
            #Add codec and timestamp
            #New table, info with dbversion     
            cursor.execute("ALTER TABLE last_downloads ADD COLUMN '%s' 'TEXT'" % 'codec')
            cursor.execute("ALTER TABLE last_downloads ADD COLUMN '%s' 'TEXT'" % 'timestamp')
            cursor.execute("CREATE TABLE info (database_version NUMERIC);")
            cursor.execute("INSERT INTO info VALUES (%d)" % 2)
        if from_version == 2 and to_version == 3:
            #Add Releasegrp
            cursor.execute("ALTER TABLE last_downloads ADD COLUMN '%s' 'TEXT'" % 'releasegrp')
            cursor.execute("ALTER TABLE last_downloads ADD COLUMN '%s' 'TEXT'" % 'subtitle')
            cursor.execute("UPDATE info SET database_version = %d WHERE database_version = %d" % (3,2))
        if from_version == 3 and to_version == 4:
            #Change IMDB_ID from INTEGER to TEXT
            cursor.execute("CREATE TABLE temp_table as select * from id_cache;")
            cursor.execute("DROP TABLE id_cache;")
            cursor.execute("CREATE TABLE id_cache (imdb_id TEXT, show_name TEXT);")
            cursor.execute("INSERT INTO id_cache select * from temp_table;")
            cursor.execute("DROP TABLE temp_table;")
            cursor.execute("UPDATE info SET database_version = %d WHERE database_version = %d" % (4,3))
        if from_version == 4 and to_version == 5:
            cursor.execute("CREATE TABLE a7id_cache (a7_id TEXT, imdb_id TEXT);")
            cursor.execute("UPDATE info SET database_version = %d WHERE database_version = %d" % (5,4))
        if from_version == 5 and to_version == 6:
            #Clear id cache once, so we don't get invalid reports about non working IMDB/A7 ID's
            cursor.execute("delete from id_cache;")
            cursor.execute("delete from a7id_cache;")
            cursor.execute("UPDATE info SET database_version = %d WHERE database_version = %d" % (6,5))
        if from_version == 6 and to_version == 7:
            #Add location on disk, so we can use it to create a preview of the subtitle.
            cursor.execute("ALTER TABLE last_downloads ADD COLUMN '%s' 'TEXT'" % 'destination')
            cursor.execute("UPDATE info SET database_version = %d WHERE database_version = %d" % (7,6))
        if from_version == 7 and to_version == 8:
            # Add episode cache table to store the episode IMDB ID
            cursor.execute("CREATE TABLE IF NOT EXISTS episode_cache (episode_imdb_id TEXT UNIQUE PRIMARY KEY, serie_os_id TEXT, season TEXT, episode TEXT);")
            cursor.execute("CREATE INDEX IF NOT EXISTS ep_index ON episode_cache(serie_os_id, season, episode);")
            cursor.execute("CREATE TABLE IF NOT EXISTS show_id_cache (imdb_id TEXT UNIQUE PRIMARY KEY, a7_id TEXT, os_id TEXT, show_name TEXT);")
            cursor.execute("INSERT OR IGNORE INTO show_id_cache (imdb_id,a7_id,show_name) SELECT id_cache.imdb_id, a7id_cache.a7_id, id_cache.show_name FROM id_cache LEFT JOIN a7id_cache ON id_cache.imdb_id = a7id_cache.imdb_id")
            cursor.execute("DROP TABLE IF EXISTS id_cache;")
            cursor.execute("DROP TABLE IF EXISTS a7id_cache;")
            cursor.execute("DROP TABLE IF EXISTS info;")
            cursor.execute("PRAGMA user_version = 8")
        if from_version == 8 or to_version == 9:
            # Drop Episode chache because we went from screenscraping to API for Opensubtitles
            cursor.execute("DROP TABLE IF EXISTS episode_cache;")
            # Drop this table because we need another layout
            cursor.execute("DROP TABLE IF EXISTS show_id_cache;")
            # Create this table again with the new layout.
            cursor.execute("CREATE TABLE IF NOT EXISTS show_id_cache (show_name TEXT UNIQUE PRIMARY KEY, imdb_id TEXT, a7_id TEXT, tvdb_id TEXT, tvdb_name TEXT);")
            cursor.execute("PRAGMA user_version = 10")
        if from_version == 9 or to_version == 10:
            # Drop Episode chache because we went from screenscraping to API for Opensubtitles
            cursor.execute("DROP TABLE IF EXISTS episode_cache;")
            # Drop this table because we need another layout
            cursor.execute("DROP TABLE IF EXISTS show_id_cache;")
            # Create this table again with the new layout.
            cursor.execute("CREATE TABLE IF NOT EXISTS show_id_cache (show_name TEXT UNIQUE PRIMARY KEY, imdb_id TEXT, a7_id TEXT, tvdb_id TEXT, tvdb_name TEXT);")
            cursor.execute("PRAGMA user_version = 10")
        if from_version == 10 or to_version == 11:
            cursor.execute("SELECT id, show_name,season,episode,quality,source,language,codec,timestamp,releasegrp,subtitle,destination FROM last_downloads")
            OldData = cursor.fetchall()
            NewTable = []
            for OldRow in OldData:
                NewRow = []
                NewRow.append(OldRow[1])
                NewRow.append(OldRow[2])
                NewRow.append(OldRow[3])
                NewRow.append(OldRow[8])
                NewRow.append(OldRow[5])
                subtitle  = OldRow[10].lower()
                if 'amazon'    in subtitle or 'amzn'  in subtitle: Distro = 'amzn'
                elif 'netflix' in subtitle or '.nf.'  in subtitle: Distro = 'nf'
                elif 'starz'   in subtitle or '.stz.' in subtitle: Distro = 'stz'
                elif 'bravo'   in subtitle or '.brv.' in subtitle: Distro = 'brv'
                else: Distro = None
                NewRow.append(Distro)
                NewRow.append(OldRow[9])
                if OldRow[4] and OldRow[4][-1:].lower() == 'p':
                    NewRow.append(OldRow[4][:-1])
                else:
                    NewRow.append(OldRow[4])
                NewRow.append(OldRow[7])
                if 'opensubtitles' in subtitle: Website = u'opensubtitles'
                elif 'addic7ed'    in subtitle: Website = u'addic7ed'
                elif 'subscene'    in subtitle: Website = u'subscene'
                else: Website = u'podnapisi'
                NewRow.append(Website)
                if OldRow[6] == 'Dutch':
                    NewRow.append(u'nl')
                else:
                    NewRow.append(u'en')
                NewRow.append(None)
                NewRow.append(OldRow[11])
                NewTable.append(NewRow)
            try:
                cursor.execute("CREATE TABLE downloaded \
                (id INTEGER PRIMARY KEY,show TEXT, season TEXT, episode TEXT,source TEXT,distro TEXT,releasegrp TEXT,quality TEXT,codec TEXT,website TEXT,language TEXT,timestamp DATETIME,title TEXT,location TEXT)")
                SQL = "INSERT INTO downloaded(show,season,episode,timestamp,source,distro,releasegrp,quality,codec,website,language,title,location) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
                Result = cursor.executemany(SQL, NewTable)
            except Exception as error:
                log.error('Problem converting database!')
                os._exit(1)
            del OldData[:]
            del NewTable[:]
            cursor.execute("DROP TABLE IF EXISTS last_downloads;")
            cursor.execute("PRAGMA user_version = 11;")
        Db.commit()
        Db.close()
        autosub.DBVERSION = version.dbversion

def getDbVersion():
    try:
        Db = sqlite3.connect(autosub.DBFILE)
        cursor=Db.cursor()
        dbversion = cursor.execute( "PRAGMA user_version").fetchone()[0]
        if dbversion == 0 :
            dbversion = cursor.execute('SELECT database_version FROM info').fetchone()[0]
        Db.close()
        return int(dbversion)
    except:
        Db.close()
        return 1

def initDb():
    #check if file is already there, if not create a database
    if os.path.exists(autosub.DBFILE):
        autosub.DBVERSION = getDbVersion()
        if autosub.DBVERSION < version.dbversion:
            upgradeDb(autosub.DBVERSION, version.dbversion)
        elif autosub.DBVERSION > version.dbversion:
            log.error( "Database version higher than this version of AutoSub supports. Update Autosub or remove database!!!")
            os._exit(1)
    else:
        createDatabase()
        # Now we read the downloaded tablke into memory for viewing in the user interface
    Db = sqlite3.connect(autosub.DBFILE)
    cursor = Db.cursor()
    SQL ="SELECT id, show,season,episode,timestamp,source,distro,releasegrp,quality,codec,website,language FROM downloaded"
    autosub.DOWNLOADED[:] = []
    try:
        autosub.DOWNLOADED = cursor.execute(SQL).fetchall()
    except Exception as error:
        log.error(error.message)
    Db.close()
    return
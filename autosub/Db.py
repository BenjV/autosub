# Autosub Db.py
#
# The Autosub DB module
# 

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
    def __init__(self):
        self.query_getId    = "SELECT imdb_id, a7_id, tvdb_id, tvdb_name FROM show_id_cache WHERE show_name = ?"
        self.query_getInfo  = "SELECT a7_id, tvdb_id,tvdb_name FROM show_id_cache WHERE imdb_id = ?"
        self.query_checkId  = "SELECT * FROM show_id_cache WHERE show_name = ?"
        self.query_updateId = "UPDATE show_id_cache SET imdb_id =?, a7_id = ?, tvdb_id = ?, tvdb_name =? WHERE show_name = ?"
        self.query_setId    = "INSERT INTO show_id_cache VALUES (?,?,?,?,?)"
        self.cursor         = autosub.DBCONNECTION.cursor()

    def getId(self, ShowName):
        try:
            Result = self.cursor.execute(self.query_getId, [ShowName]).fetchone()
            if Result:
                return Result[0],Result[1],Result[2], Result[3]
            else:
                return None, None, None, None
        except Exception as error:
            log.error('Database error: %s' % error)
            return None, None, None, None

    def getInfo(self, ImdbId):

        try:
            Result = self.cursor.execute(self.query_getInfo, [ImdbId]).fetchone()
            if Result:
                return Result[0],Result[1], Result[2]
            else:
                return None, None, None
        except Exception as error:
            log.error('Database error: %s' % error)
            return None, None, None

    def setId(self, ShowName, ImdbId, AddicId, TvdbId, TvdbName):
        try:
            Result = self.cursor.execute(self.query_checkId,[ShowName]).fetchone()
            if Result:
                self.cursor.execute(self.query_updateId,[ImdbId, AddicId, TvdbId, TvdbName, ShowName])
                autosub.DBCONNECTION.commit()
            else:
                self.cursor.execute(self.query_setId,[ShowName, ImdbId, AddicId, TvdbId, TvdbName])
                autosub.DBCONNECTION.commit()
        except Exception as error:
            log.error('Database error: %s' % error)
        return

def flushcache():
    connection=sqlite3.connect(autosub.DBFILE)
    cursor=connection.cursor()
    cursor.execute("DELETE FROM show_id_cache")
    connection.commit()
    connection.close()

class lastDown():
    def __init__(self):
        self.query_get = 'select * from last_downloads'
        self.query_set = 'insert into last_downloads values (NULL,?,?,?,?,?,?,?,?,?,?,?)'
        self.query_flush = 'delete from last_downloads'
        
    def getlastDown(self):
        connection=sqlite3.connect(autosub.DBFILE)
        connection.row_factory = dict_factory
        cursor=connection.cursor()
        cursor.execute(self.query_get)
        Llist = cursor.fetchall()
        connection.close()
        return Llist

    def setlastDown (self, Lang, **data):
        connection=sqlite3.connect(autosub.DBFILE)
        cursor=connection.cursor()
        Ldict = data['dict']

        if not 'source' in Ldict.keys():
            Ldict['source'] = None
        DstFile = os.path.join(Ldict['folder'],Ldict['file'])
        if Lang == autosub.DUTCH:
            DstFile += Ldict['NLext']
        elif Lang == autosub.ENGLISH:
            DstFile += Ldict['ENext']
        try:
            cursor.execute(self.query_set,[ 
                           Ldict['title'],
                           Ldict['season'],
                           Ldict['episode'],
                           Ldict['quality'],
                           Ldict['source'],
                           Lang,
                           Ldict['codec'],
                           Ldict['timestamp'],
                           Ldict['releasegrp'],
                           Ldict['subtitle'],
                           DstFile])
            connection.commit()
            connection.close()
        except Exception as error:
            log.error('Database error: %s' % error)
    
    def flushLastdown(self):
        connection=sqlite3.connect(autosub.DBFILE)
        cursor=connection.cursor()
        cursor.execute(self.query_flush)
        connection.commit()
        connection.close()

def createDatabase():
    #create the database
    try: 
        autosub.DBCONNECTION=sqlite3.connect(autosub.DBFILE)
        cursor=autosub.DBCONNECTION.cursor() 
        cursor.execute("CREATE TABLE show_id_cache (show_name TEXT UNIQUE PRIMARY KEY, imdb_id TEXT, a7_id TEXT, tvdb_id TEXT, tvdb_name TEXT);")
        cursor.execute("CREATE TABLE last_downloads (id INTEGER PRIMARY KEY, show_name TEXT, season TEXT, episode TEXT, quality TEXT, source TEXT, language TEXT, codec TEXT, timestamp DATETIME, releasegrp TEXT, subtitle TEXT, destination TEXT);")
        cursor.execute("PRAGMA user_version = 10")
        autosub.DBVERSION = 10
        autosub.DBCONNECTION.commit()
        print "createDatabase: Succesfully created the sqlite database"
    except:
        print "initDatabase: Could not create database, please check if AutoSub has write access to write the following file %s" %autosub.DBFILE
        os._exit(1)
    return True

def upgradeDb(from_version, to_version):
    print "upgradeDb: Upgrading database  from version %d to version %d" %(from_version, to_version)
    upgrades = to_version - from_version
    if upgrades != 1:
        print "upgradeDb: %s upgrades are required. Starting subupgrades" % upgrades
        for x in range (0, upgrades):
            upgradeDb(from_version + x, from_version + x + 1)
    else:
        cursor=autosub.DBCONNECTION.cursor()
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
        autosub.DBCONNECTION.commit()
        autosub.DBVERSION = version.dbversion

def getDbVersion():
    try:
        cursor=autosub.DBCONNECTION.cursor()
        dbversion = cursor.execute( "PRAGMA user_version").fetchone()[0]
        if dbversion == 0 :
            dbversion = cursor.execute('SELECT database_version FROM info').fetchone()[0]
        return int(dbversion)
    except:
        return 1

def initDatabase():
    #check if file is already there if not create a database
    if os.path.exists(autosub.DBFILE):
        autosub.DBCONNECTION = sqlite3.connect(autosub.DBFILE)
        autosub.DBVERSION = getDbVersion()
    else:
        createDatabase()
    autosub.DBCONNECTION.close()
    if autosub.DBVERSION < version.dbversion:
        upgradeDb(autosub.DBVERSION, version.dbversion)
    elif autosub.DBVERSION > version.dbversion:
        print "initDatabase: Database version higher than this version of AutoSub supports. Update Autosub or remove database!!!"
        os._exit(1)

import pymysql
import time
import hashlib
import struct
db_user = "test"
db_password = "cmsc711"

###
# device_key  (2^16 bitstring), XOR of did1 and did2
# latitude (float), latitude of encounter
# longitude (float), longitude of encounter
# time (datetime)
# eid, encounter id
# did1, device 1's ID
# did2, device 2's ID
###

# computes XOR of did1 and did2
def calc_key(did1, did2):
    device_key = ""
    for i in range(len(did1)):
        c1 = did1[i]
        c2 = did2[i]
        if c1 != c2:
            device_key += "1"
        else:
            device_key += "0"
    return device_key

# did is a bit string
def hash_key(did):
    did_int = int(did, 2)
    did_bytes = struct.pack("!I", did_int)
    m = hashlib.md5()
    m.update(did_bytes)
    res = int(m.hexdigest(), 16)
    #only want 16 bits
    res = res % 2**16
    return "{0:b}".format(res).zfill(16)

class SpaceTimeEncounter():
    def __init__(self, lat, lon, t, eid, device_key, infected=0):
        self.latitude = lat
        self.longitude = lon
        self.time = t
        self.eid = eid
        self.device_key = device_key
        self.infected=infected

    def __repr__(self):
        s = "LAT: " + str(self.latitude) + ", LON: " + str(self.longitude) + ", TIME: " + str(self.time) + ", EID: " + str(self.eid) + ", D_KEY1: " + str(self.device_key)
        return s

class SpaceTimeHandler():
    def __init__(self):
        self.conn = pymysql.connect(host="127.0.0.1", user=db_user, password=db_password, db="spacetime")
        self.cursor = self.conn.cursor()
        # this is for if i ever drop table
        self.create_table_string = """ CREATE TABLE STENCOUNTER (D_KEY CHAR(16) NOT NULL, LATITUDE FLOAT, LONGITUDE FLOAT, TIME DATETIME, EID CHAR(16) )"""
    
    def persist_encounter_from_dict(self, dict_ent):
        self.persist_encounter(dict_ent["latitude"], dict_ent["longitude"], dict_ent["time"], dict_ent["eid"], dict_ent["did1"], dict_ent["did2"])

    def persist_encounter(self, latitude, longitude, ent_time, eid, did1, did2):
        sql = "INSERT INTO STENCOUNTER (D_KEY, LATITUDE, LONGITUDE, TIME, EID) VALUES (%s, %s, %s, %s, %s)"
        device_key = calc_key(did1, did2)
        self.cursor.execute(sql, (device_key, latitude, longitude, ent_time.strftime('%Y-%m-%d %H:%M:%S'), eid))
        self.conn.commit()

    def _convert_res_into_ent(self, res):
        ent = SpaceTimeEncounter(lat=res[1], lon=res[2], t=res[3], eid=res[4], device_key=res[0])
        return ent

    def encounters_in(self, latitude1, latitude2, longitude1, longitude2):
        sql = "SELECT * FROM STENCOUNTER WHERE LATITUDE BETWEEN %s AND %s AND LONGITUDE BETWEEN %s AND %s"
        self.cursor.execute(sql, (latitude1, latitude2, longitude1, longitude2))
        results = self.cursor.fetchall()
        ent_list = []
        for res in results:
            ent = self._convert_res_into_ent(res)
            ent_list.append(ent)
        return ent_list

    def identify_encounter(self, did1, did2):
        device_key = calc_key(did1, did2)
        sql = "SELECT * FROM STENCOUNTER WHERE D_KEY = %s"
        self.cursor.execute(sql, (device_key))
        results = self.cursor.fetchall()
        ent_list = []
        for res in results:
            ent = self._convert_res_into_ent(res)
            ent_list.append(ent)
        return ent_list

    def get_all_encounters(self):
        sql = "SELECT * FROM STENCOUNTER"
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        ent_list = []
        for res in results:
            ent = self._convert_res_into_ent(res)
            ent_list.append(ent)
        return ent_list
    
class CausalEncounter():
    def __init__(self, eid, did1, did2, dkey):
        self.eid = eid
        self.device_key = dkey
        self.did1 = did1
        self.did2 = did2

    def __repr__(self):
        s = "EID: " + self.eid + ", DEVICE_KEY: " + self.device_key
        return s 

    # returns True if either of the stored keys is equal to hash of did
    def contains(self, did):
        hash_did = hash_key(did)
        return self.did1 == hash_did or self.did2 == hash_did
        
class CausalList():
    def __init__(self, origin, events):
        self.causal_event= None
        self.predecessors = []
        self.successors = []
        found = 0
        for e in events:
            if e.eid == origin:
                found = 1
                self.causal_event = e
            elif found == 0:
                self.predecessors.append(e)
            else:
                self.successors.append(e)

class CausalHandler():
    def __init__(self):
        self.conn = pymysql.connect(host="127.0.0.1", user=db_user, password=db_password, db="causal")
        self.cursor = self.conn.cursor()
        # this is for if i ever drop table
        self.create_table_string = """ CREATE TABLE CAUSAL (EID CHAR(16) NOT NULL, DID1 CHAR(16), DID2 CHAR(16), D_KEY CHAR(16), TIME DATETIME )"""        


    def persist_encounter(self, eid, did1, did2, timestamp):
        sql =  "INSERT INTO CAUSAL (EID, DID1, DID2, D_KEY, TIME) VALUES (%s, %s, %s, %s, %s)"
        dkey = calc_key(did1, did2)
        hashed_did1 = hash_key(did1)
        hashed_did2 = hash_key(did2)
        self.cursor.execute(sql, (eid, hashed_did1, hashed_did2, dkey, timestamp.strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
    
    def _convert_res_into_ent(self, res):
        ent = CausalEncounter(res[0], res[1], res[2], res[3])
        return ent
    
    def get_causal_list(self, eid):
        # first get devices involved in eid
        sql = "SELECT * FROM CAUSAL WHERE EID = %s"
        self.cursor.execute(sql, (eid))
        results = self.cursor.fetchall()
        if len(results) == 0:
            return []
        res = results[0]
        did1 = res[1]
        did2 = res[2]
        sql = "SELECT * FROM CAUSAL WHERE (DID1 = %s OR DID1 = %s) OR (DID2 = %s OR DID2 = %s) ORDER BY TIME"
        self.cursor.execute(sql, (did1, did2, did1, did2))
        results = self.cursor.fetchall()
        ent_list = []
        for res in results:
            ent_list.append(self._convert_res_into_ent(res))
        return CausalList(eid, ent_list)

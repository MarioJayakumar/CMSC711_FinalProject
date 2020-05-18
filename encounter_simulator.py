import entity_handler
from entity_handler import SpaceTimeEncounter
from entity_handler import CausalEncounter
import random
import datetime
    

def create_random_bit_string(length):
    return "{0:b}".format(random.getrandbits(length)).zfill(length)

class BasicEncounterGenerator():

    def __init__(self, possib_dids=None):
        self.possib_dids = possib_dids
        self.spacetime_handler = entity_handler.SpaceTimeHandler()
        self.causal_handler = entity_handler.CausalHandler()
        self.simulated = []

    def get_random_did(self):
        if self.possib_dids is None:
            return "{0:b}".format(random.getrandbits(16)).zfill(16)
        else:
            return random.choice(self.possib_dids)

    def get_random_did_pair(self):
        if self.possib_dids is None:
            d1 = self.get_random_did()
            d2 = self.get_random_did()
            return [d1, d2]
        else:
            if len(self.possib_dids) > 1:
                return random.sample(self.possib_dids, 2)
            else:
                return None

    def generate_random_encounter_between(self, did1, did2):
        eid = "{0:b}".format(random.getrandbits(16)).zfill(16)
        curr = datetime.datetime.now()
        sec = random.randrange(0, 2*8)
        curr = curr + datetime.timedelta(seconds=sec)
        e_time = curr
        latitude = round(random.uniform(-90, 90), 3)
        longitude = round(random.uniform(-90, 90), 3)
        ent_obj = {}
        ent_obj["latitude"] = latitude
        ent_obj["longitude"] = longitude
        ent_obj["time"] = e_time
        ent_obj["eid"] = eid
        ent_obj["did1"] = did1
        ent_obj["did2"] = did2
        return ent_obj

    def generate_random_encounter(self):
        dids = self.get_random_did_pair()
        did1 = dids[0]
        did2 = dids[1]
        return self.generate_random_encounter_between(did1, did2)
    
    def make_encounter_located_inside(self, et, lat1, lon1, lat2, lon2):
        if lat1 is not None:
            et["latitude"] = round(random.uniform(lat1, lat2), 3)
        if lon1 is not None:
            et["longitude"] = round(random.uniform(lon1, lon2), 3)
        return et 
    
    # resolution is within month, day
    def make_encounter_temporally_inside(self, et, year1, year2, month1, month2, day1, day2):
        if year1 is not None:
            new_year = random.randint(year1, year2)
            et["time"] = et["time"].replace(year=new_year)
        if month1 is not None:
            new_month = random.randint(month1, month2)
            et["time"] = et["time"].replace(month=new_month)
        if day1 is not None:
            new_day = random.randint(day1, day2)
            et["time"] = et["time"].replace(day=new_day)
        return et

    ###
    # if did1 defined, did2 must be defined
    # if lat1 defined, lat2 must be defined
    # ...
    ###
    def simulate_random_encounter(self, did1=None, did2=None, lat1=None, lon1=None, lat2=None, lon2=None, year1=None, year2=None, month1=None, month2=None, day1=None, day2=None, verbose=True):
        ent = None
        if did1 is None:
            ent=self.generate_random_encounter()
        else:
            ent=self.generate_random_encounter_between(did1, did2)
        if lat1 is not None or lon1 is not None:
            ent = self.make_encounter_located_inside(ent, lat1, lon2, lat2, lon2)
        if month1 is not None or day1 is not None or year1 is not None:
            ent = self.make_encounter_temporally_inside(ent, year1, year2, month1, month2, day1, day2)
        if verbose:
            print("Simulated ", str(ent))
        self.spacetime_handler.persist_encounter_from_dict(ent)
        self.causal_handler.persist_encounter(eid=ent["eid"], did1=ent["did1"], did2=ent["did2"], timestamp=ent["time"])
        self.simulated.append(ent)
        return ent

class SinglePersonEncounterGenerator():
    def __init__(self, person_id, other_ids):
        self.person_id = person_id
        self.other_ids = other_ids
        self.base_generator = BasicEncounterGenerator(other_ids)
        self.encounters = []
    
    def simulate_k_random_encounters(self, k):
        # generate k random encounters between person_id and other_ids
        for k_sub in range(k):
            other_choice = random.choice(self.other_ids)
            ent = self.base_generator.simulate_random_encounter(did1=self.person_id, did2=other_choice)
            self.encounters.append(ent)
    
    def simulate_sequential_random_encounters(self, min_month=1):
        max_month = 12
        for month in range(min_month, max_month+1):
            other_device = random.choice(self.other_ids)
            ent = self.base_generator.simulate_random_encounter(did1=self.person_id, did2=other_device, month1=month, month2=max_month)
            self.encounters.append(ent)

class InfectionEncounterGenerator():
    def __init__(self, other_ids, infection_chance, region):
        self.other_ids = other_ids
        self.infected_ids = []
        self.infected_ids.append(self.other_ids[0])
        self.infection_chance = infection_chance
        self.lat1, self.lon1, self.lat2, self.lon2 = region
        self.base_generator = BasicEncounterGenerator(other_ids)
        self.infection_encounters = [] # trace of infection events, ordered by time
    
    def simulate_k_infection_encounters(self, k, verbose):
        # simulate until we have reached the end of the time or k infections occured
        curr_year = 2005
        curr_month = 1
        while curr_year < 2020 and len(self.infection_encounters) < k:
            did_pair = self.base_generator.get_random_did_pair()
            did1 = did_pair[0]
            did2 = did_pair[1]
            ent = self.base_generator.simulate_random_encounter(did1=did1, did2=did2, lat1=self.lat1, lon1=self.lon1, lat2=self.lat2, lon2=self.lon2, year1=curr_year, year2=curr_year, month1=curr_month, month2=curr_month, verbose=verbose)
            if (did1 in self.infected_ids) != (did2 in self.infected_ids):
                # roll the dice on whether to infect or not
                infect_occurs = random.random() < self.infection_chance
                if infect_occurs:
                    self.infection_encounters.append(ent)
                    if did1 not in self.infected_ids:
                        self.infected_ids.append(did1)
                    else:
                        self.infected_ids.append(did2)
            curr_month += 1
            if curr_month > 12:
                curr_month = 1
                curr_year += 1

    def simulate_separate_infection(self, first, second, third):
        # simulate first infecting second, then first infecting third
        curr_year = 2020
        curr_month = 1
        first_day = 10
        second_day = 20
        ent = self.base_generator.simulate_random_encounter(did1=first, did2=second, lat1=self.lat1, lon1=self.lon1, lat2=self.lat2, lon2=self.lon2, year1=curr_year, year2=curr_year, month1=curr_month, month2=curr_month, day1=first_day, day2=first_day)
        self.infected_ids.append(first)
        self.infected_ids.append(second)
        self.infection_encounters.append(ent)
        eid1 = ent["eid"]
        ent = self.base_generator.simulate_random_encounter(did1=first, did2=third, lat1=self.lat1, lon1=self.lon1, lat2=self.lat2, lon2=self.lon2, year1=curr_year, year2=curr_year, month1=curr_month, month2=curr_month, day1=second_day, day2=second_day)
        self.infected_ids.append(third)
        self.infection_encounters.append(ent)
        eid2 = ent["eid"]
        return second, eid1, third, eid2


    def reset(self):
        self.infected_ids = []
        self.infected_ids.append(self.other_ids[0])
        self.infection_encounters = []
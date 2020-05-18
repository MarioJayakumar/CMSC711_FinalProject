# possible queries that an epidemiologist may create
import entity_handler

spacetime_handler = entity_handler.SpaceTimeHandler()
causal_handler = entity_handler.CausalHandler()

def XOR(did1, did2):
    device_key = ""
    for i in range(len(did1)):
        c1 = did1[i]
        c2 = did2[i]
        if c1 != c2:
            device_key += "1"
        else:
            device_key += "0"
    return device_key

def set_intersection(set1, set2):
    temp_map = {}
    for s in set1:
        temp_map[s] = 1
    intersection_set = []
    for s in set2:
        if s in temp_map:
            intersection_set.append(s)
    return intersection_set

# union of set1 and set2 without duplicates
def set_join(set1, set2):
    temp_map = {}
    union = []
    for s in set1:
        if s not in temp_map:
            union.append(s)
            temp_map[s] = 1
    for s in set2:
        if s not in temp_map:
            union.append(s)
            temp_map[s] = 1
    return union

# what is the exact encounter that occured between device1, device2
# (did2,did2) -> List(SpaceTimeEncounters)
def what_encounter(device1, device2):
    encounter_list = spacetime_handler.identify_encounter(device1, device2)
    for enc in encounter_list:
        print(enc)

# if eid involved an infected patient did1, determine all possible infection encounters afterwards
def possibly_infected_after(did1, eid):
    possib_list = causal_handler.get_causal_list(eid)
    did2 = XOR(did1, possib_list.causal_event.device_key)
    infect_dids = []
    for succ in possib_list.successors:
        if succ.contains(did1):
            infect_dids.append(XOR(did1, succ.device_key))
        else:
            infect_dids.append(XOR(did2, succ.device_key))
    return infect_dids
        

# given a did, and latest encounter, determine all who are at risk of infection and possible infectors
def possibly_infected_before(did1, eid):
    possib_list = causal_handler.get_causal_list(eid)
    did2 = XOR(did1, possib_list.causal_event.device_key)
    infect_dids = []
    for pred in possib_list.predecessors:
        if pred.contains(did1):
            infect_dids.append(XOR(did1, pred.device_key))
        else:
            infect_dids.append(XOR(did2, pred.device_key))
    return infect_dids

def devices_encountered_before(did1, eid):
    possib_list = causal_handler.get_causal_list(eid)
    did2 = XOR(did1, possib_list.causal_event.device_key)
    devices = [did2]
    for pred in possib_list.predecessors:
        if pred.contains(did1):
            devices.append(XOR(did1, pred.device_key))
    return devices

# did1 and did2 both tested positive but never encountered each other, who infected both of them
# this can only identify a single device that was missing and infected both did1 and did2
def link_between_devices(did1, did2, eid1, eid2):
    pred1 = devices_encountered_before(did1, eid1)
    pred2 = devices_encountered_before(did2, eid2)
    # set intersection of pred1 and pred2
    return set_intersection(pred1, pred2)

class Node:
    def __init__(self, eid, did1, did2, parent):
        self.did1 = did1
        self.did2 = did2
        self.eid = eid
        self.parent = parent
        self.children = []
        self.infected=False

    def contains(self, did):
        return self.did1 == did or self.did2 == did

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.did1 == other.did1 and self.did2 == other.did2 and self.eid == other.eid 
        return False

    def __hash__(self):
        return hash((self.did1, self.did2, self.eid))

def generate_neighbor_nodes(root_node):
    did1 = root_node.did1
    did2 = root_node.did2
    eid = root_node.eid
    pred = causal_handler.get_causal_list(eid).predecessors
    neighbors = []
    for enc in pred:
        if enc.contains(did1):
            new_node = Node(enc.eid, did1, XOR(enc.device_key, did1), root_node)
            neighbors.append(new_node)
            root_node.children.append(new_node)
        else:
            new_node = Node(enc.eid, did2, XOR(enc.device_key, did2), root_node)
            neighbors.append(new_node)
            root_node.children.append(new_node)
    return neighbors

# path of infection between two devices based on two encounters
def infection_path_between_encounters(root1, root2, max_k):
    devices1 = [root1.did1, root1.did2]
    devices2 = [root2.did1, root2.did2]
    neighbors1 = [root1]
    neighbors2 = [root2]
    all_nodes1 = neighbors1
    all_nodes2 = neighbors2
    k = 0
    found = False
    global_visited = {}
    for k in range(max_k):
        device_intersection = set_intersection(devices1, devices2)
        node_intersection = set_intersection(all_nodes1, all_nodes2)
        if len(node_intersection) > 0:
            found = True
            break
        else:
            newNeighbors1 = []
            newNeighbors2 = []
            new_devices1 = []
            new_devices2 = []
            for n in neighbors1:
                if n not in global_visited:
                    global_visited[n] = True
                    generated = generate_neighbor_nodes(n)
                    for g in generated:
                        new_devices1.append(g.did1)
                        new_devices1.append(g.did2)
                    newNeighbors1 = set_join(newNeighbors1, generated)
            for n in neighbors2:
                if n not in global_visited:
                    global_visited[n] = True
                    generated = generate_neighbor_nodes(n)
                    for g in generated:
                        new_devices2.append(g.did1)
                        new_devices2.append(g.did2)
                    newNeighbors2 = set_join(newNeighbors2, generated)
            devices1 = set_join(devices1, new_devices1)
            devices2 = set_join(devices2, new_devices2)
            neighbors1 = newNeighbors1
            all_nodes1 = set_join(all_nodes1, neighbors1)
            neighbors2 = newNeighbors2
            all_nodes2 = set_join(all_nodes2, neighbors2)
    if found:
        root_infector = set_intersection(devices1, devices2)[0]
        print("Common Infector: ", root_infector)
        commonNode1 = None
        commonNode2 = None
        for n in all_nodes1:
            if n.contains(root_infector):
                commonNode1 = n
        for n in all_nodes2:
            if n.contains(root_infector):
                commonNode2 = n
                commonNode2.children = [commonNode1]
        path1 = []
        path2 = []
        while commonNode1 != None:
            commonNode1.infected = True
            path1.append(commonNode1)
            commonNode1 = commonNode1.parent
        while commonNode2 != None:
            commonNode2.infected = True
            path2.append(commonNode2)
            commonNode2 = commonNode2.parent
        return (path1, path2)
    else:
        return ([],[])


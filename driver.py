import entity_handler
import encounter_simulator
import epidemiology


def test_link_between():
    first_id = encounter_simulator.create_random_bit_string(16)
    second_id = encounter_simulator.create_random_bit_string(16)
    third_id = encounter_simulator.create_random_bit_string(16)
    device_pool = [first_id, second_id, third_id]

    infection_gen = encounter_simulator.InfectionEncounterGenerator(device_pool, .50, (0,0,20,20))
    _, eid1, _, eid2 = infection_gen.simulate_separate_infection(first_id, second_id, third_id)

    # link between second id and third id should be first id
    print("1st id is ", first_id)
    print("2nd id is ", second_id)
    print("3rd id is ", third_id)
    res = epidemiology.link_between_devices(second_id, third_id, eid1, eid2)
    if len(res) == 0:
        print("Results is empty")
    else:
        if res[0] == first_id:
            print("Success, found link as ", res[0])
        else:
            print("Wrong, found link ", res[0])

def test_possibly_infected_before():
    first_id = encounter_simulator.create_random_bit_string(16)
    device_pool = []
    for _ in range(15):
        device_pool.append(encounter_simulator.create_random_bit_string(16))
    single_gen = encounter_simulator.SinglePersonEncounterGenerator(first_id, device_pool)
    single_gen.simulate_sequential_random_encounters()
    last_enc = single_gen.encounters[-1]
    # assert that every element in encounters is contained in epidemiology before
    before_ids = epidemiology.possibly_infected_before(first_id, last_enc["eid"])
    simulated_ids = []
    for s in single_gen.encounters:
        if s != last_enc:
            if s["did1"] == first_id:
                simulated_ids.append(s["did2"])
            else:
                simulated_ids.append(s["did1"])
    error = 0
    if len(simulated_ids) - 1 > len(before_ids):
        print("Before IDs too short")
        error = 1
    for s in simulated_ids:
        if s not in before_ids:
            print(s, " not found in infected_before")
            error = 1
    if error == 0:
        print("SUCCESS")
        for s in before_ids:
            print("Encountered ", s)

def draw_visited_encounters(rootnode1, rootnode2):
    def node_name(n):
        return "DID1: " + n.did1 + ", DID2: " + n.did2
    f = open("search_result.txt", "w")
    f.write("digraph G {\n")
    frontier = [rootnode1, rootnode2]
    visited = {}
    visited[rootnode1.eid] = True
    visited[rootnode2.eid] = True
    while len(frontier) > 0:
        curr = frontier.pop()
        if curr == rootnode1:
            f.write("\"{0}\" [style=filled, fillcolor=red];\n".format(node_name(curr)))
        elif curr == rootnode2:
            f.write("\"{0}\" [style=filled, fillcolor=blue];\n".format(node_name(curr)))
        elif curr.infected:
            f.write("\"{0}\" [style=filled, fillcolor=green];\n".format(node_name(curr)))
        for c in curr.children:
            s = "\"{0}\" -> \"{1}\";\n".format(node_name(curr), node_name(c))
            f.write(s)
            visited[c.eid] = True
            frontier.append(c)
    f.write("}\n")
    f.close()

def test_infection_tree():
    device_pool = []
    for _ in range(7):
        device_pool.append(encounter_simulator.create_random_bit_string(16))
    single_gen = encounter_simulator.InfectionEncounterGenerator(device_pool, 0.99, (0,0,10,10))
    original_infector = device_pool[0]
    print("Original Infector: ", original_infector)
    single_gen.simulate_k_infection_encounters(k=6, verbose=True)
    for f in single_gen.infection_encounters:
        print(f)
    last_encounter1 = single_gen.infection_encounters[-2]
    last_encounter2 = single_gen.infection_encounters[-1]
    rootnode1 = epidemiology.Node(last_encounter1["eid"], last_encounter1["did1"], last_encounter1["did2"], None)
    rootnode2 = epidemiology.Node(last_encounter2["eid"], last_encounter2["did1"], last_encounter2["did2"], None)
    path1, path2 = epidemiology.infection_path_between_encounters(rootnode1, rootnode2, 20)
    print("PATH1")
    i = 0
    for p in path1:
        i += 1
        print("NUM: ", i, "EID: ", p.eid, " D1: ", p.did1, " D2: ", p.did2)
    print("PATH2")
    i = 0
    for p in path2:
        i += 1
        print("NUM: ", i, "EID: ", p.eid, " D1: ", p.did1, " D2: ", p.did2)

    draw_visited_encounters(rootnode1, rootnode2)

test_infection_tree()
            


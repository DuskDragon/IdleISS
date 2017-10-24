import random
import json

#TODO: Distance floodfill?

def flood(node):
    if(node.flooded):
        return
    node.flooded = True
    for x in node.connections:
        flood(x)

def floodfill(node_list):
    flood(node_list[0])
    for x in node_list:
        if x.flooded == False: # found an unconnected node, eject
            return False
    # no unconnected nodes were found
    return True

def drain(node_list):
    for x in node_list: #reset flood state
        x.flooded = False

class SolarSystem(object):
    def __init__(self, random_state, universe, security, name, const, region):
        if universe.name_exists(name):
            raise ValueError("SolarSystem __init__: "+name+" already exists")
        self.name = name
        universe.register_name(self.name)

        self.constellation = const
        self.region = region
        self.entitytype = "System"
        self.bordertype = "Solar"
        self.security = security
        self.rand = random_state
        self.connections = []
        self.id = universe.get_next_system_id()
        self.flooded = False

    def __str__(self):
        connections_str = ""
        for x in self.connections:
            connections_str += " " + str(x.name)
        return "idleiss.universe.SolarSystem: " + str(self.name) + " Connections: " + connections_str

    def connection_exists(self, entity):
        return entity in self.connections

    def add_connection(self, system):
        if self.connection_exists(system):
            return False # may want to change this return type (means already connected)
        self.connections.append(system)
        if system.connection_exists(self):
            raise ValueError("1-way System Connection: "+system.name+" to "+self.name)
        system.connections.append(self)
        return True # connection added

class Constellation(object):
    def __init__(self, random_state, universe, systems, security, name, region):
        if universe.name_exists(name):
            raise ValueError("Constellation __init__: "+name+" already exists")
        self.name = name
        universe.register_name(self.name)

        self.entitytype = "Constellation"
        self.systems = systems
        self.security = security
        if len(self.systems) > universe.systems_per_constellation:
            raise ValueError("Constellation __init__: "+name+": too many systems")
        if len(self.systems) < universe.systems_per_constellation:
            if security != "Null":
                raise ValueError("Constellation __init__: "+name+": too few systems for non-nullsec")
            for x in range(universe.systems_per_constellation - len(self.systems)):
                new_sys = SolarSystem(random_state, universe, security, universe.generate_unused_nullsec_name(), self.name, region)
                self.systems.append(new_sys)
        #print("idleiss.universe._build_universe: calling stitch nodes on: "+region+": "+self.name+": systems: "+str(len(self.systems)))#DEBUG LINE
        self.systems = universe.stitch_nodes(self.systems)
        self.rand = random_state
        self.region = region
        self.connections = []
        self.id = universe.get_next_constellation_id()
        self.flooded = False

    def __str__(self):
        connections_str = ""
        for x in self.connections:
            connections_str += " " + str(x.name)
        return "idleiss.universe.Constellation: " + str(self.name) + " Connections: " + connections_str

    def connection_exists(self, constellation):
        return constellation in self.connections

    def add_connection(self, constellation, connect_type="Constellation", extra=False):
        if self.connection_exists(constellation) and extra == False:
            return False # may want to change this return type (means already connected)
        elif self.connection_exists(constellation) and extra == True:
            pass # TODO:may need to add something else here
        else: #self.connection_exists(constellation) is false
            self.connections.append(constellation)
            if constellation.connection_exists(self):
                raise ValueError("1-way Constellation Connection: "+constellation.name+" to "+self.name)
            constellation.connections.append(self)
        #TODO: change this to find the LEAST CONNECTED system (maybe) instead of random choice
        dest = self.rand.choice(constellation.systems)
        jumpoff = self.rand.choice(self.systems)
        dest.add_connection(jumpoff)
        dest.bordertype = connect_type
        jumpoff.bordertype = connect_type
        return True # connection added

class Region(object):
    def __init__(self, random_state, universe, constellations, name, security):
        if universe.name_exists(name):
            raise ValueError("Region __init__: "+name+" already exists")
        self.name = name
        universe.register_name(self.name)

        self.entitytype = "Region"
        self.constellations = constellations
        self.security = security
        if len(self.constellations) > universe.constellations_per_region:
            raise ValueError("Region __init__: "+name+": too many constellations")
        if len(self.constellations) < universe.constellations_per_region:
            if security != "Null":
                raise ValueError("Region __init__: "+name+": too few constellations for non-nullsec")
            for x in range(universe.constellations_per_region - len(self.constellations)):
                new_const = Constellation(random_state, universe, [], security, universe.generate_unused_nullsec_name(), self.name)
                self.constellations.append(new_const)
        #print("idleiss.universe._build_universe: calling stitch nodes on: "+self.name+": constellations: "+str(len(self.constellations)))#DEBUG LINE
        self.constellations = universe.stitch_nodes(self.constellations)
        self.rand = random_state
        self.connections = []
        self.border_edge_systems = []
        self.id = universe.get_next_constellation_id()
        self.flooded = False

    def __str__(self):
        connections_str = ""
        for x in self.connections:
            connections_str += " " + str(x.name)
        return "idleiss.universe.Region: " + str(self.name) + " Connections: " + connections_str

    def connection_exists(self, region):
        return region in self.connections

    def add_connection(self, region, extra=False):
        if self.connection_exists(region) and extra == False:
            return False # may want to change this return type (means already connected)
        elif self.connection_exists(region) and extra == True:
            pass # TODO:may need to add something else here
        else: #self.connection_exists(region) is false
            self.connections.append(region)
            if region.connection_exists(self):
                raise ValueError("1-way Region Connection: "+region.name+" to "+self.name)
            region.connections.append(self)
        #TODO: change this to find the LEAST CONNECTED const (maybe) instead of random choice
        dest = self.rand.choice(region.constellations)
        jumpoff = self.rand.choice(self.constellations)
        dest.add_connection(jumpoff, connect_type="Region", extra=extra)

        return True # connection added

class Universe(object):
    _required_keys = [
        'Universe Seed', #top level keys
        'System Count',
        'Constellation Count',
        'Systems Per Constellation',
        'Region Count',
        'Constellations Per Region',
        'Systems Per Region',
        'High Security Systems',
        'High Security Regions',
        'Low Security Systems',
        'Low Security Regions',
        'Null Security Systems',
        'Null Security Regions',
        'Connectedness',
        'Low-High Bonus Connections',
        'Low-Null Bonus Connections',
        'High-Null Bonus Connections',
        'Null-Low Depth Ratio',
        'Universe Structure'
    ]
    _required_region_keys = [
        'Security',
        'Orphan Systems',
        'Special Systems',
        'Constellations'
    ]

    def __init__(self, filename=None):
        """
        generates a universe with #systems, #constellations and #regions
        using connectedness as a rough guide to how linked nodes are within a collection
        """
        self.rand = random
        self.used_names = []
        self.regions = []
        self.constellations = []
        self.systems = []
        self.current_unused_system_id = 0
        self.current_unused_constellation_id = 0
        self.current_unused_region_id = 0
        if filename:
            self.load(filename)

    def get_next_system_id(self):
        ret_val = self.current_unused_system_id
        self.current_unused_system_id += 1
        return ret_val

    def get_next_constellation_id(self):
        ret_val = self.current_unused_constellation_id
        self.current_unused_constellation_id += 1
        return ret_val

    def get_next_region_id(self):
        ret_val = self.current_unused_region_id
        self.current_unused_region_id += 1
        return ret_val

    def _missing_universe_keys(self, universe_data):
        uni_required_keys = set(self._required_keys)
        uni_provided_keys = set(universe_data.keys())
        missing = uni_required_keys - uni_provided_keys
        if missing:
            return ', '.join(uni_required_keys - uni_provided_keys)
        for region in universe_data['Universe Structure']:
            region_required_keys = set(self._required_region_keys)
            region_provided_keys = set(universe_data['Universe Structure'][region].keys())
            missing = region_required_keys - region_provided_keys
            if missing:
                return str(region)+": "+', '.join(missing)
        return False

    def load(self, filename):
        with open(filename) as fd:
            raw_data = json.load(fd)
        self._load(raw_data)

    def _load(self, raw_data):
        missing = self._missing_universe_keys(raw_data)
        if missing:
            raise ValueError(str(missing)+' not found in config')

        self.rand.seed(raw_data['Universe Seed'])
        self.system_count_target = raw_data['System Count']
        self.constellation_count_target = raw_data['Constellation Count']
        self.region_count_target = raw_data['Region Count']
        self.connectedness = raw_data['Connectedness']
        self.systems_per_constellation = raw_data["Systems Per Constellation"]
        self.constellations_per_region = raw_data["Constellations Per Region"]
        self.low_high_bonus = raw_data["Low-High Bonus Connections"]
        self.low_null_bonus = raw_data["Low-Null Bonus Connections"]
        self.high_null_bonus = raw_data["High-Null Bonus Connections"]
        self.null_low_depth = raw_data["Null-Low Depth Ratio"]

        self._verify_config_settings(raw_data)
        #TODO: config file is verified except for rigidly defined structures

        self._build_universe(raw_data)

    def _verify_config_settings(self, raw_data):
        universe_structure = raw_data['Universe Structure']

        if raw_data["System Count"] != raw_data["Constellation Count"] * raw_data["Systems Per Constellation"]:
            raise ValueError("System Count does not equal 'Constellation Count'*'Systems Per Constellation'")
        if raw_data["System Count"] != raw_data["Region Count"] * raw_data["Systems Per Region"]:
            raise ValueError("System Count does not equal 'Region Count'*'Systems Per Region'")
        if raw_data["System Count"] != raw_data["Region Count"] * raw_data["Constellations Per Region"] * raw_data["Systems Per Constellation"]:
            raise ValueError("System Count does not equal 'Region Count'*'Constellations Per Region'*'Systems Per Constellation'")
        if raw_data["High Security Systems"] != raw_data['High Security Regions'] * raw_data['Systems Per Region']:
            raise ValueError("High Security System count does not match highsec_regions*systems_per_region")
        if raw_data["Low Security Systems"] != raw_data['Low Security Regions'] * raw_data['Systems Per Region']:
            raise ValueError("Low Security System count does not match lowsec_regions*systems_per_region")
        if raw_data["Null Security Systems"] != raw_data['Null Security Regions'] * raw_data['Systems Per Region']:
            raise ValueError("Null Security System count does not match nullsec_regions*systems_per_region")
        if raw_data["Region Count"] != raw_data['High Security Regions'] + raw_data['Low Security Regions'] + raw_data['Null Security Regions']:
            raise ValueError("Region counts do not match with total region count")
        #count actual regions
        if raw_data["Region Count"] != len(universe_structure):
            raise ValueError("Region Count in config: "+str(raw_data["Region Count"])+" does not match actual region count: "+str(len(universe_structure)))

        highsec_regions, lowsec_regions, nullsec_regions = 0,0,0

        for region in universe_structure:
            region_data = universe_structure[region]
            if region_data['Security'] == "High":
                highsec_regions += 1
            elif region_data['Security'] == "Low":
                lowsec_regions += 1
            elif region_data['Security'] == "Null":
                nullsec_regions += 1

        if raw_data["High Security Regions"] != highsec_regions:
            raise ValueError("Highsec Region Count is "+str(highsec_regions)+" but should be: "+str(raw_data["High Security Regions"]))
        if raw_data["Low Security Regions"] != lowsec_regions:
            raise ValueError("Lowsec Region Count is "+str(lowsec_regions)+" but should be: "+str(raw_data["Low Security Regions"]))
        if raw_data["Null Security Regions"] != nullsec_regions:
            raise ValueError("Nullsec Region Count is "+str(nullsec_regions)+" but should be: "+str(raw_data["Null Security Regions"]))

        if self.low_high_bonus > 1.0 or self.low_high_bonus < 0.0:
            raise ValueError("Low-High Bonus connections must be in the range [0,1]")
        if self.low_null_bonus+self.high_null_bonus > 1.0 or self.low_null_bonus+self.high_null_bonus < 0.0:
            raise ValueError("Low-Null Bonus+High-Null Bonus must be in the range [0,1]")
        if self.high_null_bonus > self.low_null_bonus:
            raise ValueError("Low-High Bonus must be less than Low-Null Bonus")

        if self.null_low_depth < 1.0:
            raise ValueError("Null-Low Depth Ratio cannot be less than 1")

        #verify low/high sec space have fully named systems:
        for region in universe_structure:
            region_data = universe_structure[region]
            if type(region_data["Orphan Systems"]) != list:
                raise ValueError(region+": orphan systems is not a list.")
            if type(region_data["Special Systems"]) != dict:
                raise ValueError(region+": special systems is not a dictionary.")
            if region_data['Security'] == "High" or region_data['Security'] == "Low":
                if region_data["Orphan Systems"] != []:
                    raise ValueError(region+" is a non-nullsec region with orphan systems which is not allowed.")
                if raw_data["Constellations Per Region"] != len(region_data["Constellations"]):
                    raise ValueError(region+": contains "+str(len(region_data["Constellations"]))+" the expected value is "+str(raw_data["Constellations Per Region"]))
                for constellation in region_data['Constellations']:
                    if raw_data['Systems Per Constellation'] != len(region_data['Constellations'][constellation]):
                        raise ValueError(region+': '+constellation+': contains '+str(len(region_data['Constellations'][constellation]))+' systems when it should have '+str(raw_data['Systems Per Constellation']))
            #null is more customiziable because it is filled in with random sys-names
            elif region_data['Security'] == "Null":
                if raw_data["Constellations Per Region"] < len(region_data["Constellations"]):
                    raise ValueError(region+": contains "+str(len(region_data["Constellations"]))+" the expected value is less than or equal to "+str(raw_data["Constellations Per Region"]))
                for constellation in region_data['Constellations']:
                    if raw_data['Systems Per Constellation'] < len(region_data['Constellations'][constellation]):
                        raise ValueError(region+': '+constellation+': contains '+str(len(region_data['Constellations'][constellation]))+' systems when it should have less than or equal to '+str(raw_data['Systems Per Constellation']))
            else:
                raise ValueError(region+": contiains invalid Security rating.")

        #TODO remove DEBUG initial name loading \/ \/ \/ \/
        systems_verified = 0
        constellations_verified = 0
        regions_verified = 0
        #start loading names into the huge name list
        for region in universe_structure:
            region_data = universe_structure[region]
            self.register_name(region)
            regions_verified += 1
            for orphan_sys in region_data["Orphan Systems"]:
                self.register_name(orphan_sys)
                systems_verified += 1
            for special_sys in region_data["Special Systems"]:
                self.register_name(special_sys)
                systems_verified += 1
            for constellation in region_data["Constellations"]:
                self.register_name(constellation)
                constellations_verified += 1
                for system in region_data["Constellations"][constellation]:
                    self.register_name(system)
                    systems_verified += 1

        print("\nSuccessfully imported the following:")
        print(str(regions_verified)+" regions")
        print("    "+str(highsec_regions)+" High Security")
        print("    "+str(lowsec_regions)+" Low Security")
        print("    "+str(nullsec_regions)+" Null Security")
        print(str(constellations_verified)+" constellations")
        print(str(systems_verified)+" systems")

        self.used_names = []
        #TODO remove initial name loading ^^^^^^^^^^

    def register_name(self, name):
        if self.name_exists(name):
            raise ValueError("Universe generation: entity name exists: "+name)
        else:
            self.used_names.append(name)

    def name_exists(self, name):
        return name in self.used_names

    def generate_networkx(self, node_list):
        """
        Debugging function which uses NetworkX (python mathematics tool)
        NetworkX is a fully python implementation so don't use HUGE graphs
        it's 225x slower than graph-tool (g-t is implemented as a C++ library with python wrapper)
        """
        import networkx as nx
        G = nx.Graph()
        connection_list = []
        orphan_list = []
        for x in node_list:
            if len(x.connections) == 0:
                orphan_list.append(x.name)
            for y in x.connections:
                if x.id > y.id:
                    connection_list.append((x.name,y.name,))
                else: # y > x:
                    connection_list.append((y.name,x.name,))
        pruned_list = set(connection_list)
        # add collected nodes
        G.add_edges_from(pruned_list)
        G.add_nodes_from(orphan_list)
        ## TODO: clean up when not needed
        ## debug info
        #print("Nodes: "+str(G.number_of_nodes())+", Edges: "+str(G.number_of_edges()))
        #import matplotlib.pyplot as plt
        #plt.subplot(111)
        #nx.draw_networkx(G, with_labels=True)
        #plt.show()
        return G

    def generate_graph_tool(self, node_list):
        """
        Debugging function which uses graph-tool (python mathematics tool)
        graph-tool is a C++ implementation with a python wrapper
        it's 225x faster than NetworkX (NetworkX is python only)
        """
        import graph_tool as gtool
        graph = gtool.Graph(directed=False)
        connection_list = []
        orphan_list = []
        name_list = list(range(len(node_list)))
        vprop = graph.new_vertex_property("string")
        vertex_list = list(graph.add_vertex(len(node_list)))
        for x in node_list:
            name_list[x.id] = x.name
            if len(x.connections) == 0:
                orphan_list.append(x.name)
            for y in x.connections:
                if x.id > y.id:
                    connection_list.append((x.id,y.id,))
                else: # y > x:
                    connection_list.append((y.id,x.id,))
        #prune redundant connections
        pruned_list = set(connection_list)
        # name nodes
        for x in range(len(vertex_list)):
            vprop[vertex_list[x]] = name_list[x]
        # assign properties as a dict value
        graph.vertex_properties["name"]=vprop
        # add collected edges
        for x in pruned_list:
            graph.add_edge(vertex_list[x[0]],vertex_list[x[1]])
        return graph

    def _build_universe(self, verified_config):
        regions = verified_config["Universe Structure"]
        these_region = []
        for region in regions: #dict
            constellations = regions[region]["Constellations"]
            these_const = []
            for constellation in constellations: #list/dict
                systems = constellations[constellation]
                these_sys = []
                for system in systems:
                    #generate system
                    new_sys = SolarSystem(self.rand, self, regions[region]["Security"], system, constellation, region)
                    these_sys.append(new_sys)
                    if type(systems) == dict: #defined const
                        pass #TODO: connect pre-defined connected systems
                # generate const
                these_sys = self.constellation_stitch(these_sys)
                new_const = Constellation(self.rand, self, these_sys, regions[region]["Security"], constellation, region)
                these_const.append(new_const)
            # generate region
            these_const = self.region_stitch(these_const)
            new_region = Region(self.rand, self, these_const, region, regions[region]["Security"])
            these_region.append(new_region)
            #TODO: Force in guaranteed system names

        #build final connected listing
        #   connect regions using region-specific connection method
        these_region = self.galaxy_stitch(these_region)
        #TODO: Force in Special Systems
        #verify all regions are connected
        self.regions = self.stitch_nodes(these_region)
        for region in self.regions:
            for constellation in region.constellations:
                self.constellations.append(constellation)
                for system in constellation.systems:
                    self.systems.append(system)

    def galaxy_stitch(self, region_list):
        """
        The galaxy will have a highsec center, lowsec inner layer, and nullsec outer layer
        Highsec will be formed using a central region with a ring of outer regions
        Lowsec will be outside this, nullsec outside that
        """
        # collect regions into categories
        highsec_regions = []
        lowsec_regions = []
        nullsec_regions = []
        for region in region_list:
            if region.security == "High":
                highsec_regions.append(region)
            elif region.security == "Low":
                lowsec_regions.append(region)
            elif region.security == "Null":
                nullsec_regions.append(region)
            else:
                raise ValueError("galaxy_stitch: invalid security status: "+str(region.name))
        # first pick a highsec region to act as the central region
        central_highsec_region = self.rand.choice(highsec_regions)
        highsec_ring = highsec_regions
        highsec_ring.remove(central_highsec_region)
        # form the ring using the self.connectedness metric to determine
        #   when a spoke or arc exists
        for x in range(len(highsec_ring)):
            region = highsec_ring[x]
            edge_chance = min(float(self.connectedness)/2.0,1.0)
            # check if there is only one region
            if len(highsec_ring) == 1:
                region.add_connection(central_highsec_region)
                continue
            # determine which node is on the "rightside"
            rightside = 0
            if x == len(highsec_ring)-1: #last node
                rightside = highsec_ring[0]
            else:
                rightside = highsec_ring[x+1]
            # roll for spoke
            if self.rand.random() <= edge_chance:
                region.add_connection(central_highsec_region)
            # roll for rightside arc
            if self.rand.random() <= edge_chance:
                region.add_connection(rightside)
        # add additional connections at random according to connectedness
        if len(highsec_regions) != 1:
            existing_connections = self.count_edges(highsec_regions)
            target_connections = int(float(self.connectedness)*float(len(highsec_regions)))
            needed_additional_connections = max(target_connections-existing_connections,0)
            for x in range(needed_additional_connections):
                source, dest = self.rand.sample(highsec_regions, 2)
                source.add_connection(dest, extra=True)
        # highsec is formed
        # now to create lowsec ring
        for x in range(len(lowsec_regions)):
            region = lowsec_regions[x]
            edge_chance = min(float(self.connectedness)/2.0,1.0)
            inward = 0
            rightside = 0
            #determine if there are more lowsec regions than highsec for the rings
            #determine spoke target
            lowsec_pos = (x+1)
            if len(highsec_ring) == 0:
                inward = central_highsec_region
            elif len(lowsec_regions) >= len(highsec_ring):
                inward = highsec_ring[int(lowsec_pos/len(highsec_ring))]
            else: #len(lowsec_regions) < len(highsec_ring):
                inner_start = int(x*len(highsec_ring)/len(lowsec_regions))
                inner_end = inner_start + int(len(highsec_ring)/len(lowsec_regions))
                inward = self.rand.choice(highsec_ring[inner_start:inner_end])
            #determine rightside
            if x == len(lowsec_regions)-1: #last node
                rightside = highsec_ring[0]
            else:
                rightside = highsec_ring[x+1]
            #roll for spoke
            if self.rand.random() <= edge_chance:
                region.add_connection(inward)
            #roll for righside arc
            if self.rand.random() <= edge_chance:
                region.add_connection(rightside)
        # add additional connections at random according to connectedness
        if len(lowsec_regions) != 1:
            existing_connections = self.count_edges(lowsec_regions)
            target_connections = int(float(self.connectedness)*float(len(highsec_regions)))
            needed_additional_connections = max(target_connections-existing_connections,0)
            for x in range(needed_additional_connections):
                source = self.rand.choice(lowsec_regions)
                if self.rand.random() <= self.low_high_bonus and len(highsec_regions) > 0: #highsec
                    dest = self.rand.choice(highsec_regions)
                else: # lowsec
                    source, dest = self.rand.sample(lowsec_regions, 2)
                source.add_connection(dest, extra=True)
        # lowsec is formed
        # now to create nullsec rings
        nullsec_ring_count = max(int(len(nullsec_regions)/(self.null_low_depth*len(lowsec_regions))),1)
        #how many layers of nullsec? layer_count = int(null/(1.5*lowsec_count))
        #so if there are 45 nullsec and 10 lowsec
        #there should be 3 layers of nullsec
        nullsec_ring_list = list(range(nullsec_ring_count))
        regions_per_ring = int(len(nullsec_regions)/nullsec_ring_count)
        last_used = 0
        for x in range(nullsec_ring_count):
            nullsec_ring_list[x] = nullsec_regions[x*regions_per_ring:(x*regions_per_ring)+(regions_per_ring-1)]
            last_used = (x*regions_per_ring)+(regions_per_ring-1)
        remainder_regions = nullsec_regions[last_used::]
        #randomly insert remainder_regions into all rings
        for region in remainder_regions:
            random_ring = self.rand.choice(nullsec_ring_list)
            random_position = self.rand.randint(0,len(random_ring))
            random_ring.insert(random_position, region)
        for ring_number in range(len(nullsec_ring_list)):
            this_ring = nullsec_ring_list[ring_number]
            for region_number in range(len(this_ring)):
                region = this_ring[region_number]
                edge_chance = min(float(self.connectedness)/2.0,1.0)
                inward = 0
                righward = 0
                #determine spoke target
                if ring_number == 0: # innermost null ring, inward connects to lowsec
                    #determine if there are more nullsec regions in ring than lowsec ring
                    if len(lowsec_regions) == 0:
                        if len(highsec_ring) == 0: # no highsec ring
                            inward = central_highsec_region
                        else: # highsec ring exists
                            if len(this_ring) >= len(highsec_ring):
                                inward = highsec_ring[int((region_number+1)/len(highsec_ring))]
                            else: #len(this_ring) < len(highsec_ring):
                                inner_start = int(region_number*len(highsec_ring)/len(this_ring))
                                inner_end = inner_start + int(len(highsec_ring)/len(this_ring))
                                inward = self.rand.choice(highsec_ring[inner_start:inner_end])
                    else: # lowsec exists
                        if len(this_ring) >= len(lowsec_regions):
                            inward = lowsec_regions[int((region_number+1)/len(lowsec_regions))]
                        else: #len(this_ring) < len(lowsec_regions):
                            inner_start = int(region_number*len(lowsec_regions)/len(this_ring))
                            inner_end = inner_start + int(len(lowsec_regions)/len(this_ring))
                            inward = self.rand.choice(lowsec_regions[inner_start:inner_end])
                else: # this null ring only connects to null for inward
                    inner_ring = nullsec_ring_list[ring_number-1]
                    if len(this_ring) >= len(inner_ring):
                        inward = inner_ring[int((region_number+1)/len(inner_ring))]
                    else: #len(this_ring) < len(inner_ring):
                        inner_start = int(region_number*len(inner_ring)/len(this_ring))
                        inner_end = inner_start + int(len(inner_ring)/len(this_ring))
                        inward = self.rand.choice(inner_ring[inner_start:inner_end])
                #determine rightside
                if region_number == len(this_ring)-1: #last node
                    rightside = this_ring[0]
                else:
                    rightside = this_ring[region_number+1]
                #roll for spoke
                if self.rand.random() <= edge_chance:
                    region.add_connection(inward)
                #roll for righside arc
                if self.rand.random() <= edge_chance:
                    region.add_connection(rightside)
                # add additional connections at random according to connectedness
                if len(nullsec_regions) != 1:
                    existing_connections = self.count_edges(nullsec_regions)
                    target_connections = int(float(self.connectedness)*float(len(nullsec_regions)))
                    needed_additional_connections = max(target_connections-existing_connections,0)
                    for extra_connection_num in range(needed_additional_connections):
                        source = self.rand.choice(nullsec_regions)
                        rolled_chance = self.rand.random()
                        if rolled_chance <= self.high_null_bonus and len(highsec_regions) > 0: #highsec
                            dest = self.rand.choice(highsec_regions)
                        elif rolled_chance <= self.high_null_bonus+self.low_null_bonus and len(lowsec_regions) > 0: #lowsec
                            dest = self.rand.choice(lowsec_regions)
                        else: # nullsec
                            source, dest = self.rand.sample(nullsec_regions, 2)
                        source.add_connection(dest, extra=True)
                    # end of for loop for additional connections
                #end of if statement preventing additional connections if nullsec_region count is 1
            #end of for loop iterating over regions in current nullsec ring
        #end of for loop iterating over all nullsec rings
        # nullsec is formed
        # return finished galaxy
        return region_list

    def region_stitch(self, constellation_list):
        return constellation_list

    def constellation_stitch(self, system_list):
        return system_list

    def stitch_nodes(self, node_list):
        """
        guarantees that a node_list will pass floodfill
        does not add more edges than needed
        """
        if len(node_list) < 2:
            raise ValueError("idleiss.universe.stitch_nodes: must have at least two systems for a connection. List provided was: "+str(node_list))
        # floodfill
        if len(node_list[0].connections) == 0: #floodfill will start on orphan, avoid this
            node_list[0].add_connection(self.rand.choice(node_list[1:]))
        while not floodfill(node_list):
            #floodfill failed, find failed nodes:
            valid_nodes = []
            orphan_nodes = []
            disjoint_nodes = []
            for x in node_list:
                if len(x.connections) == 0:
                    orphan_nodes.append(x)
                elif x.flooded:
                    valid_nodes.append(x)
                else: # not flooded, not orphan, must be disjoint
                    disjoint_nodes.append(x)
            #first pin disjoint graphs to valid nodes
            if len(disjoint_nodes) > 0:
                disjoint_nodes[0].add_connection(self.rand.choice(valid_nodes))
                drain(node_list)
                continue #go around again
            #next pin all orphans, there are only ophans remaining
            for x in range(len(orphan_nodes)): #include already processed orphans
                orphan_nodes[x].add_connection(self.rand.choice((valid_nodes + orphan_nodes[:x])))
            drain(node_list)
        #end of floodfill
        drain(node_list)
        return node_list

    def count_edges(self, node_list):
        connection_list = []
        for x in node_list:
            for y in x.connections:
                if x.id > y.id:
                    connection_list.append((x.id,y.id,))
                else: # y > x:
                    connection_list.append((y.id,x.id,))
        pruned_list = set(connection_list)
        return len(pruned_list)

    def generate_alphanumeric(self):
        valid_characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        return self.rand.choice(valid_characters)

    def _generate_nullsec_name(self):
        #example D-PNP9, 6VDT-H, OWXT-5, 16P-PX, CCP-US
        #always uppercase letters
        #5 characters with a dash in the middle somewhere
        dash_position = self.rand.randint(1,4)
        letters = ''.join((self.generate_alphanumeric() for x in range(5)))
        return letters[0:dash_position] + '-' + letters[dash_position::]

    def generate_unused_nullsec_name(self):
        possible_name = self._generate_nullsec_name()
        while self.name_exists(possible_name):
            possible_name = self._generate_nullsec_name()
        return possible_name

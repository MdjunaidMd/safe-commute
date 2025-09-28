# data_prep.py
import os
import math
from osmnx import distance

GRAPH_DIR = "graph_data"
os.makedirs(GRAPH_DIR, exist_ok=True)

cities = {
    "bengaluru": {"place": "Bengaluru, Karnataka, India", "center": (12.9716, 77.5946)},
    "mysuru":    {"place": "Mysuru, Karnataka, India",    "center": (12.2958, 76.6394)}
}

def make_demo_graph(city_key, center):
    """Create a tiny demo graph (grid) with lat/lon and safety attributes"""
    import networkx as nx
    lat0, lon0 = center
    G = nx.DiGraph()
    # 5x5 grid -> 25 nodes
    size = 5
    step = 0.002  # degree step approx ~200m
    node_id = 0
    for i in range(size):
        for j in range(size):
            node_id += 1
            lat = lat0 + (i - size//2) * step
            lon = lon0 + (j - size//2) * step
            G.add_node(node_id, x=lon, y=lat)
    # connect edges (right and down)
    for n in list(G.nodes()):
        # compute grid coords from node id
        idx = n - 1
        r = idx // size
        c = idx % size
        # right neighbor
        if c < size-1:
            nid = n + 1
            length = step * 111000  # rough meters
            # random-ish safety
            safety = 0.4 + ((r+c) % 5) * 0.12
            G.add_edge(n, nid, length=length, safety=min(1.0, safety))
            G.add_edge(nid, n, length=length, safety=min(1.0, safety))
        # down neighbor
        if r < size-1:
            nid = n + size
            length = step * 111000
            safety = 0.5 + ((r*c) % 5) * 0.1
            G.add_edge(n, nid, length=length, safety=min(1.0, safety))
            G.add_edge(nid, n, length=length, safety=min(1.0, safety))
    out_path = os.path.join(GRAPH_DIR, f"graph_{city_key}_demo.graphml")
    print("Saving demo graph to", out_path)
    nx.write_graphml(G, out_path)
    return out_path

def prepare_with_osmnx():
    import osmnx as ox
    print("OSMnx available — using real OSM graphs (may take a few minutes).")
    for key, meta in cities.items():
        place = meta["place"]
        print("Downloading/creating graph for:", place)
        G = ox.graph_from_place(place, network_type='walk', simplify=True)
        G = distance.add_edge_lengths(G)

        # create simple safety attributes
        import random
        nodes = list(G.nodes())
        hotspots = random.sample(nodes, min(5, len(nodes)))
        for u, v, k, d in G.edges(keys=True, data=True):
            lit = d.get('lit', None)
            d['lighting'] = 1.0 if (lit and str(lit).lower() in ['yes','street']) else 0.35
            midx = ((G.nodes[u]['x'] + G.nodes[v]['x'])/2, (G.nodes[u]['y'] + G.nodes[v]['y'])/2)
            # crude crime influence based on distance to hotspots
            d['crime'] = min(1.0, min([1.0 / (1 + math.hypot(midx[0]-G.nodes[h]['x'], midx[1]-G.nodes[h]['y'])) for h in hotspots]))
            d['safety'] = max(0.0, (d['lighting']*0.7 + (1-d['crime'])*0.3))
        out_path = os.path.join(GRAPH_DIR, f"graph_{key}.graphml")
        print("Saving graph to", out_path)
        ox.save_graphml(G, out_path)
    print("OSM graph prep finished.")

def main():
    try:
        import osmnx as ox
    except Exception as e:
        print("OSMnx not available or failed to import. Falling back to demo graphs.")
        for key, meta in cities.items():
            make_demo_graph(key, meta["center"])
        print("Demo graphs created. You can continue with the backend using demo graphs.")
        return

    # if osmnx import succeeded, run prepare_with_osmnx
    prepare_with_osmnx()

if __name__ == "__main__":
    main()

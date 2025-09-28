# app.py (updated)
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import osmnx as ox
import networkx as nx
from networkx.exception import NetworkXNoPath
import uvicorn
import csv
import math
import requests
from typing import List, Dict

app = FastAPI()

# Allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

GRAPH_DIR = "graph_data"
GRAPHS = {}
REPORTS_FILE = "reports/reports.csv"

# ----------------- Helpers -----------------
def list_available_cities():
    cities = []
    if not os.path.exists(GRAPH_DIR):
        return cities
    for fn in os.listdir(GRAPH_DIR):
        if fn.startswith("graph_") and fn.endswith(".graphml"):
            key = fn[len("graph_"):-len(".graphml")]
            cities.append(key)
    return sorted(cities)

def load_graph(city_key: str):
    if city_key in GRAPHS:
        return GRAPHS[city_key]

    filename = f"graph_{city_key}.graphml"
    path = os.path.join(GRAPH_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph not found for {city_key}: {path}")

    print(f"Loading graph: {path}")
    G = ox.load_graphml(path)
    GRAPHS[city_key] = G
    return G

def nearest_node(G, lat, lon):
    # ox.distance.nearest_nodes expects (G, X (lon), Y (lat))
    return ox.distance.nearest_nodes(G, lon, lat)

def compute_distance_and_time(G, path_nodes):
    total_length = 0.0
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        edge_data = G.get_edge_data(u, v, 0)
        length = float(edge_data.get("length", 0.0))
        total_length += length

    distance_km = total_length / 1000.0
    avg_speed_kmh = 30.0
    travel_time_hr = distance_km / avg_speed_kmh
    travel_time_min = travel_time_hr * 60.0
    return round(distance_km, 2), round(travel_time_min, 1)

def nodes_to_coords(G, nodes):
    # returns coordinates as [lat, lon] for each node
    return [[float(G.nodes[n]['y']), float(G.nodes[n]['x'])] for n in nodes]

def ensure_latlon(coords: List[List[float]]) -> List[List[float]]:
    """
    Ensure coords are in [lat, lon] order.
    Heuristic: if first value abs > 90 (likely lon), swap.
    """
    out = []
    for pt in coords or []:
        if not pt or len(pt) < 2:
            continue
        a = float(pt[0])
        b = float(pt[1])
        # if first value looks like longitude (abs > 90) then swap
        if abs(a) > 90 and abs(b) <= 90:
            out.append([b, a])
        else:
            out.append([a, b])
    return out

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def clean_value(val):
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            if not math.isfinite(val):
                return None
            return float(val)
        return str(val)
    except:
        return None

# ----------------- Reports / Safety -----------------
def load_reports():
    reports = []
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    lat, lon, note = float(row[0]), float(row[1]), row[2]
                    reports.append((lat, lon, note))
                except:
                    continue
    return reports

# ----------------- Overpass API -----------------
def query_overpass_nearby(lat: float, lon: float, radius_m: int = 2000) -> List[Dict]:
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{lat},{lon})["amenity"~"police|hospital|fire_station"];
      way(around:{radius_m},{lat},{lon})["amenity"~"police|hospital|fire_station"];
      relation(around:{radius_m},{lat},{lon})["amenity"~"police|hospital|fire_station"];
    );
    out center tags;
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        res = requests.post(url, data={"data": query}, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print("Overpass request error:", e)
        return []

    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        lat_val, lon_val = None, None
        if el.get("type") == "node":
            lat_val, lon_val = el.get("lat"), el.get("lon")
        else:
            center = el.get("center")
            if center:
                lat_val, lon_val = center.get("lat"), center.get("lon")
        if lat_val is None or lon_val is None:
            continue
        places.append({
            "lat": float(lat_val),
            "lon": float(lon_val),
            "tags": tags
        })
    return places

# ----------------- Safety breakdown -----------------
def compute_safety_breakdown(lat_lon_list: List[List[float]], probe_radius_m=300):
    if not lat_lon_list:
        return {"reports_nearby": 0, "safe_places_nearby": 0, "police": 0, "hospital": 0, "fire_station": 0}

    lats = [p[0] for p in lat_lon_list]
    lons = [p[1] for p in lat_lon_list]
    centroid_lat = sum(lats) / len(lats)
    centroid_lon = sum(lons) / len(lons)

    places = query_overpass_nearby(centroid_lat, centroid_lon, radius_m=600)
    police = sum(1 for p in places if (p.get("tags", {}).get("amenity") or "").lower() == "police")
    hospital = sum(1 for p in places if (p.get("tags", {}).get("amenity") or "").lower() == "hospital")
    fire_station = sum(1 for p in places if (p.get("tags", {}).get("amenity") or "").lower() == "fire_station")
    safe_places_nearby = police + hospital + fire_station

    reports = load_reports()
    reports_nearby = 0
    for (r_lat, r_lon, _) in reports:
        for p in lat_lon_list:
            dist = haversine_meters(p[0], p[1], r_lat, r_lon)
            if dist <= 150:
                reports_nearby += 1
                break

    return {
        "reports_nearby": reports_nearby,
        "safe_places_nearby": safe_places_nearby,
        "police": police,
        "hospital": hospital,
        "fire_station": fire_station
    }

def compute_safety_score_from_breakdown(breakdown: Dict):
    score = 70.0
    score += min(20.0, (breakdown.get("police", 0) + breakdown.get("hospital", 0)) * 6.0)
    score += min(6.0, breakdown.get("fire_station", 0) * 3.0)
    score -= min(60.0, breakdown.get("reports_nearby", 0) * 10.0)
    score = max(0.0, min(100.0, score))
    return int(round(score))

# ----------------- API Routes -----------------
@app.get("/cities")
def get_cities():
    return {"cities": list_available_cities()}

@app.get("/route")
def get_routes(city: str = Query("bengaluru"),
               src_lat: float = Query(...), src_lon: float = Query(...),
               dst_lat: float = Query(...), dst_lon: float = Query(...)):
    try:
        G = load_graph(city)
        s = nearest_node(G, src_lat, src_lon)
        t = nearest_node(G, dst_lat, dst_lon)

        # Fastest path (by length)
        try:
            fastest_nodes = nx.dijkstra_path(G, s, t, weight="length")
        except NetworkXNoPath:
            fastest_nodes = []
        fast_dist, fast_time = compute_distance_and_time(G, fastest_nodes) if fastest_nodes else (0.0, 0.0)
        fastest_coords = nodes_to_coords(G, fastest_nodes) if fastest_nodes else []

        # Compute risk_cost on edges (safe default if missing)
        for u, v, k, d in G.edges(keys=True, data=True):
            length = float(d.get("length", 1.0))
            safety = float(d.get("safety", 0.5)) if d.get("safety") is not None else 0.5
            risk_multiplier = (1.0 - safety) * 5.0
            d["risk_cost"] = length * (1.0 + risk_multiplier)

        # Safest path (by risk_cost)
        try:
            safest_nodes = nx.dijkstra_path(G, s, t, weight="risk_cost")
        except NetworkXNoPath:
            safest_nodes = []

        safe_dist, safe_time = compute_distance_and_time(G, safest_nodes) if safest_nodes else (0.0, 0.0)
        safest_coords = nodes_to_coords(G, safest_nodes) if safest_nodes else []

        # If safest is empty, fall back to fastest (so UI always has a line)
        if not safest_coords and fastest_coords:
            print("Safest path not found — falling back to fastest path for display")
            safest_coords = list(fastest_coords)
            safe_dist, safe_time = fast_dist, fast_time

        # Debug prints so you can see what's happening in terminal
        print("FASTEST coords length:", len(fastest_coords))
        print("SAFEST coords length:", len(safest_coords))
        print("FASTEST sample:", fastest_coords[:5])
        print("SAFEST sample:", safest_coords[:5])

        # Safety breakdown & scoring
        fastest_break = compute_safety_breakdown(fastest_coords)
        safest_break = compute_safety_breakdown(safest_coords)
        fastest_score = compute_safety_score_from_breakdown(fastest_break)
        safest_score = compute_safety_score_from_breakdown(safest_break)

        # Ensure coordinates are [lat, lon] for Leaflet before returning
        fastest_coords_out = ensure_latlon(fastest_coords)
        safest_coords_out = ensure_latlon(safest_coords)

        return {
            "fastest": {
                "coords": fastest_coords_out,
                "distance_km": fast_dist,
                "time_min": fast_time,
                "safety_score": fastest_score,
                "breakdown": fastest_break
            },
            "safest": {
                "coords": safest_coords_out,
                "distance_km": safe_dist,
                "time_min": safe_time,
                "safety_score": safest_score,
                "breakdown": safest_break
            }
        }
    except Exception as e:
        print("ERROR in /route:", e)
        return {"error": str(e)}

@app.post("/report")
def report_unsafe(lat: float, lon: float, note: str = ""):
    try:
        os.makedirs("reports", exist_ok=True)
        with open(REPORTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([lat, lon, note])
        return {"status": "ok", "lat": lat, "lon": lon, "note": note}
    except Exception as e:
        print("ERROR in /report:", e)
        return {"error": str(e)}

@app.get("/panic")
def panic(city: str = Query("bengaluru"),
          lat: float = Query(...), lon: float = Query(...)):
    try:
        places = query_overpass_nearby(lat, lon, radius_m=2000)

        if not places:
            try:
                G = load_graph(city)
                node = nearest_node(G, lat, lon)
                return {
                    "safe_zones": [
                        {
                            "type": "road",
                            "name": "Nearest Road Node",
                            "lat": float(G.nodes[node]['y']),
                            "lon": float(G.nodes[node]['x']),
                            "address": None,
                            "phone": None,
                            "distance_m": round(haversine_meters(lat, lon,
                                            float(G.nodes[node]['y']), float(G.nodes[node]['x'])), 1)
                        }
                    ]
                }
            except Exception as e:
                print("Fallback graph fail:", e)
                return {"safe_zones": []}

        results = []
        for p in places:
            plat, plon = p["lat"], p["lon"]
            dist_m = haversine_meters(lat, lon, plat, plon)
            tags = p.get("tags", {})
            name = tags.get("name")
            phone = tags.get("phone") or tags.get("contact:phone") or tags.get("phone:mobile")

            addr = tags.get("addr:full")
            if not addr:
                street = tags.get("addr:street", "")
                houseno = tags.get("addr:housenumber", "")
                city_t = tags.get("addr:city", "")
                addr_parts = [x for x in [houseno, street, city_t] if x]
                addr = ", ".join(addr_parts) if addr_parts else None

            typ = tags.get("amenity") or tags.get("building") or tags.get("office") or "unknown"

            results.append({
                "type": clean_value(typ),
                "name": clean_value(name) or "Unnamed",
                "lat": float(plat),
                "lon": float(plon),
                "address": clean_value(addr),
                "phone": clean_value(phone),
                "distance_m": round(float(dist_m), 1)
            })

        results = sorted(results, key=lambda x: x["distance_m"])
        return {"safe_zones": results[:12]}

    except Exception as e:
        print("ERROR in /panic:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

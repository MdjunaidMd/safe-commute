import os
import osmnx as ox

# Ensure graph_data folder exists
os.makedirs("graph_data", exist_ok=True)

# Add all cities/districts you want
cities = {
    "bengaluru": "Bengaluru, India",
    "mysuru": "Mysuru, India",
    "tumkur": "Tumkur, Karnataka, India",
    "bengalururural": "Bengaluru Rural, Karnataka, India",
    "mandya": "Mandya, Karnataka, India",
    "hosur": "Hosur, Tamil Nadu, India"
}

for key, place in cities.items():
    print(f"📥 Downloading road network for {place}...")
    try:
        # Download drivable road network
        G = ox.graph_from_place(place, network_type="drive")

        # Save as graphml
        filename = f"graph_data/graph_{key}.graphml"
        ox.save_graphml(G, filename)
        print(f"✅ Saved {filename}")
    except Exception as e:
        print(f"❌ Failed to download {place}: {e}")

print("🎉 All graphs downloaded and saved successfully!")

// App.jsx
import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Popup,
  useMap,
} from "react-leaflet";
import axios from "axios";
import L from "leaflet";
import "./App.css";

// Default Leaflet Marker fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom icons
const policeIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/emoji/48/police-car-light.png",
  iconSize: [32, 32],
});
const hospitalIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/color/48/hospital-2.png",
  iconSize: [32, 32],
});
const fireIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/color/48/fire-station.png",
  iconSize: [32, 32],
});
const reportIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/color/48/error--v1.png",
  iconSize: [28, 28],
});

// ✅ Start (Green Pin) & End (Red Pin)
const startIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/color/48/40C057/marker.png",
  iconSize: [40, 40],
  iconAnchor: [20, 40],
});
const endIcon = new L.Icon({
  iconUrl: "https://img.icons8.com/color/48/FA5252/marker.png",
  iconSize: [40, 40],
  iconAnchor: [20, 40],
});

// ---------- Landing Page ----------
function LandingPage({ onStart }) {
  return (
    <div className="landing">
      <h1>🛡️ Safe Commute Planner</h1>
      <p>
        Travel confidently with AI-powered safest routes.
        Designed especially for women’s safety with SOS, nearby police & hospital alerts,
        and community safety reports.
      </p>

      <div className="features">
        <div>🚔 Police & Hospitals on your route</div>
        <div>🛡️ Safest path suggestions</div>
        <div>⚠️ Report unsafe spots</div>
        <div>👩 Focused on women’s safety</div>
      </div>

      <button className="start-btn" onClick={onStart}>
        🚀 Go to Map
      </button>
    </div>
  );
}

// ---------- Auto-fit Bounds ----------
function MapBounds({ fastest, safest }) {
  const map = useMap();
  let coords = [];
  if (fastest?.coords?.length > 0) coords = coords.concat(fastest.coords);
  if (safest?.coords?.length > 0) coords = coords.concat(safest.coords);

  useEffect(() => {
    if (coords.length > 0) {
      console.log("📍 Fitting map to route:", coords.length, "points");
      map.fitBounds(coords, { padding: [40, 40] });
    }
  }, [fastest, safest]);

  return null;
}

// ---------- Helpers ----------
function getEmergencyNumber(zone) {
  if (zone.phone) return zone.phone;
  if (!zone.type) return "112";
  const t = zone.type.toLowerCase();
  if (t.includes("police")) return "100";
  if (t.includes("hospital")) return "108";
  if (t.includes("fire")) return "101";
  return "112";
}

function getSafetyLabel(score) {
  if (score >= 75) return "safe";
  if (score >= 40) return "moderate";
  return "unsafe";
}

// ---------- Main App ----------
function App() {
  const [showMap, setShowMap] = useState(false);
  const [cities, setCities] = useState([]);
  const [city, setCity] = useState("bengaluru");
  const [srcQuery, setSrcQuery] = useState("");
  const [dstQuery, setDstQuery] = useState("");
  const [srcCoords, setSrcCoords] = useState(null);
  const [dstCoords, setDstCoords] = useState(null);
  const [fastest, setFastest] = useState(null);
  const [safest, setSafest] = useState(null);
  const [activeTab, setActiveTab] = useState("safest");
  const [safeZones, setSafeZones] = useState([]);
  const [reports, setReports] = useState([]);

  // Fetch cities
  useEffect(() => {
    const loadCities = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/cities");
        setCities(res.data.cities || []);
      } catch (err) {
        console.error("Error fetching cities:", err);
      }
    };
    loadCities();
  }, []);

  // Geocoding
  const geocodeLocation = async (query, cityName) => {
    if (!query) return null;
    try {
      const res = await axios.get("https://nominatim.openstreetmap.org/search", {
        params: { q: `${query}, ${cityName}, India`, format: "json", limit: 1 },
      });
      if (res.data.length > 0) {
        return {
          lat: parseFloat(res.data[0].lat),
          lon: parseFloat(res.data[0].lon),
          display: res.data[0].display_name,
        };
      }
      return null;
    } catch (err) {
      console.error("Geocoding error:", err);
      return null;
    }
  };

  // Fetch routes
  const fetchRoutes = async () => {
    const src = await geocodeLocation(srcQuery, city);
    const dst = await geocodeLocation(dstQuery, city);
    if (!src || !dst) {
      alert("Invalid source or destination");
      return;
    }
    setSrcCoords(src);
    setDstCoords(dst);
    try {
      const res = await axios.get("http://127.0.0.1:8000/route", {
        params: {
          city,
          src_lat: src.lat,
          src_lon: src.lon,
          dst_lat: dst.lat,
          dst_lon: dst.lon,
        },
      });

      console.log("✅ API Response:", res.data);
      console.log("🚗 Fastest coords:", res.data.fastest.coords);
      console.log("🛡️ Safest coords:", res.data.safest.coords);


      const fastestData = {
        ...res.data.fastest,
        safety_label: getSafetyLabel(res.data.fastest?.safety_score || 0),
      };
      const safestData = {
        ...res.data.safest,
        safety_label: getSafetyLabel(res.data.safest?.safety_score || 0),
      };

      setFastest(fastestData);
      setSafest(safestData);
      setSafeZones([]);
    } catch (err) {
      console.error(err);
      alert("Error fetching routes");
    }
  };

  // SOS
  const triggerPanic = async () => {
    if (!srcCoords) return alert("Set a source first!");
    try {
      const res = await axios.get("http://127.0.0.1:8000/panic", {
        params: { city, lat: srcCoords.lat, lon: srcCoords.lon },
      });
      if (res.data && res.data.safe_zones) {
        setSafeZones(res.data.safe_zones);
      } else {
        alert("No safe locations found");
      }
    } catch (err) {
      console.error(err);
      alert("Panic API failed");
    }
  };

  // Report unsafe
  const reportUnsafe = async () => {
    if (!dstCoords) return alert("Set a destination first!");
    try {
      await axios.post("http://127.0.0.1:8000/report", null, {
        params: { lat: dstCoords.lat, lon: dstCoords.lon, note: "Unsafe area" },
      });
      setReports([...reports, { lat: dstCoords.lat, lon: dstCoords.lon }]);
      alert("Unsafe spot reported!");
    } catch (err) {
      console.error(err);
      alert("Report API failed");
    }
  };

  const getIconForZone = (type) => {
    if (!type) return L.Icon.Default;
    const t = type.toLowerCase();
    if (t.includes("police")) return policeIcon;
    if (t.includes("hospital")) return hospitalIcon;
    if (t.includes("fire")) return fireIcon;
    return L.Icon.Default;
  };

  // ---------- Render ----------
  if (!showMap) {
    return <LandingPage onStart={() => setShowMap(true)} />;
  }

  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      {/* Header */}
      <div className="header">
        <h2>🛡️ Safe Commute Planner</h2>
        <select value={city} onChange={(e) => setCity(e.target.value)}>
          {cities.map((c) => (
            <option key={c} value={c}>{c.toUpperCase()}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Enter Source"
          value={srcQuery}
          onChange={(e) => setSrcQuery(e.target.value)}
        />
        <input
          type="text"
          placeholder="Enter Destination"
          value={dstQuery}
          onChange={(e) => setDstQuery(e.target.value)}
        />
        <button onClick={fetchRoutes}>Get Routes</button>
      </div>

      {/* Map */}
      <MapContainer center={[12.9716, 77.5946]} zoom={13} className="leaflet-map">
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        {/* ✅ Start & End markers */}
        {srcCoords && (
          <Marker position={[srcCoords.lat, srcCoords.lon]} icon={startIcon} />
        )}
        {dstCoords && (
          <Marker position={[dstCoords.lat, dstCoords.lon]} icon={endIcon} />
        )}

        {/* ✅ Draw routes */}
        {fastest?.coords && (
          <Polyline positions={fastest.coords} color="red" weight={4} dashArray="6" opacity={0.8} />
        )}
        {safest?.coords && (
          <Polyline positions={safest.coords} color="green" weight={6} opacity={0.9} />
        )}

        {/* Safe zones */}
        {safeZones.map((z, idx) => (
          <Marker key={`safe-${idx}`} position={[z.lat, z.lon]} icon={getIconForZone(z.type)}>
            <Popup>
              <div>
                <h4>{z.type?.toUpperCase() || "SAFE"}</h4>
                <p><b>{z.name || "Unnamed"}</b></p>
                <p>📍 {z.address || "N/A"}</p>
                <p>☎️ {z.phone || getEmergencyNumber(z)}</p>
                <p>📏 {z.distance_m ? `${z.distance_m} m` : ""}</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Reports */}
        {reports.map((r, idx) => (
          <Marker key={`report-${idx}`} position={[r.lat, r.lon]} icon={reportIcon}>
            <Popup>⚠️ Reported Unsafe Spot</Popup>
          </Marker>
        ))}

        {/* Auto-fit bounds */}
        <MapBounds fastest={fastest} safest={safest} />
      </MapContainer>

      {/* Route Details Panel */}
      {(fastest || safest) && (
        <div className="info-panel">
          <div className="tabs">
            <button className={activeTab==="safest"?"active":""} onClick={()=>setActiveTab("safest")}>🛡️ Safest</button>
            <button className={activeTab==="fastest"?"active":""} onClick={()=>setActiveTab("fastest")}>🚗 Fastest</button>
          </div>
          {activeTab === "fastest" && fastest && (
            <div className={`route-card ${fastest.safety_label}`}>
              <h4>🚗 Fastest</h4>
              <p>{fastest.distance_km} km, {fastest.time_min} min</p>
              <p>Safety: {fastest.safety_score}/100</p>
            </div>
          )}
          {activeTab === "safest" && safest && (
            <div className={`route-card ${safest.safety_label}`}>
              <h4>🛡️ Safest</h4>
              <p>{safest.distance_km} km, {safest.time_min} min</p>
              <p>Safety: {safest.safety_score}/100</p>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="legend">
        <p><span style={{ background: "red" }}></span> Fastest Route</p>
        <p><span style={{ background: "green" }}></span> Safest Route</p>
      </div>

      {/* Floating Buttons */}
      <div style={{
        position: "absolute", bottom: 20, right: 20,
        display: "flex", flexDirection: "column", gap: "12px", zIndex: 3000,
      }}>
        <button className="sos-btn" onClick={triggerPanic}>SOS</button>
        <button className="report-btn" onClick={reportUnsafe}>📝</button>
      </div>
    </div>
  );
}

export default App;

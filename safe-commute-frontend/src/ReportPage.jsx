// ReportPage.jsx
import React, { useState } from "react";
import "./ReportPage.css";

function ReportPage() {
  const [selectedType, setSelectedType] = useState("");
  const [details, setDetails] = useState("");
  const [file, setFile] = useState(null);

  const categories = [
    { id: "lighting", label: "Poor Lighting", icon: "💡", desc: "Broken streetlights or dark areas" },
    { id: "harassment", label: "Harassment", icon: "🚨", desc: "Inappropriate behavior or catcalling" },
    { id: "unsafe", label: "Unsafe Area", icon: "⚠️", desc: "General safety concerns or suspicious activity" },
    { id: "infra", label: "Infrastructure", icon: "🛠️", desc: "Broken roads, missing signs, or barriers" },
  ];

  const handleSubmit = () => {
    alert(`Incident Reported!\nType: ${selectedType}\nDetails: ${details}`);
    // 🔗 TODO: Call backend API (/report) with data
  };

  return (
    <div className="report-container">
      {/* Header */}
      <h2 className="title">📝 Report Incident</h2>
      <p className="subtitle">Help improve community safety</p>

      {/* Location */}
      <div className="location-box">
        📍 <b>Indiranagar, Bengaluru</b> <span className="time">⏱ {new Date().toLocaleTimeString()}</span>
      </div>

      {/* Categories */}
      <div className="categories">
        {categories.map((c) => (
          <div
            key={c.id}
            className={`category-card ${selectedType === c.id ? "active" : ""}`}
            onClick={() => setSelectedType(c.id)}
          >
            <span className="icon">{c.icon}</span>
            <div>
              <h4>{c.label}</h4>
              <p>{c.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Details */}
      <textarea
        placeholder="Describe what happened in more detail (optional)"
        value={details}
        onChange={(e) => setDetails(e.target.value)}
      ></textarea>

      {/* Upload */}
      <div className="upload-section">
        <label className="upload-btn">
          📷 Photo
          <input type="file" hidden onChange={(e) => setFile(e.target.files[0])} />
        </label>
        <button className="upload-btn">🎤 Voice Note</button>
      </div>

      {/* Submit */}
      <button className="submit-btn" onClick={handleSubmit}>
        🚀 Report Incident
      </button>
    </div>
  );
}

export default ReportPage;

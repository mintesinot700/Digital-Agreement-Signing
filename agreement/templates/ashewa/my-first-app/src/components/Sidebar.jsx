// src/components/Sidebar.js
import React from "react";
import { FaChartBar, FaUsers, FaCog, FaUser, FaSignOutAlt, FaArrowLeft } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    [ACCESS_TOKEN, REFRESH_TOKEN].forEach((item) =>
      localStorage.removeItem(item)
    );
    navigate("/login");
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-main">Ashewa</div>
        <div className="logo-sub">Ecomerece and Technology solutions.</div>
      </div>
      <div className="sidebar-section">
        <div className="sidebar-section-title">MENU</div>
        <nav className="sidebar-nav">
          <div className="sidebar-item" onClick={() => navigate("/admin/dashboard")}>
            <FaArrowLeft className="sidebar-icon" /> Back to Dashboard
          </div>
          <div
            className={`sidebar-item ${activeTab === "detail" ? "active" : ""}`}
            onClick={() => setActiveTab("detail")}
          >
            <FaChartBar className="sidebar-icon" /> Agreement Detail
          </div>
          <div
            className="sidebar-item"
            onClick={() => navigate("/admin/dashboard?tab=users")}
          >
            <FaUsers className="sidebar-icon" /> Manage Users
          </div>
        </nav>
      </div>
      <div className="sidebar-section sidebar-others-section">
        <div className="sidebar-section-title">OTHERS</div>
        <nav className="sidebar-nav">
          <div className="sidebar-item">
            <FaCog className="sidebar-icon" /> Settings
          </div>
          <div className="sidebar-item">
            <FaUser className="sidebar-icon" /> PDF_load
          </div>
          <div className="sidebar-item" onClick={handleLogout}>
            <FaSignOutAlt className="sidebar-icon" /> Log Out
          </div>
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;

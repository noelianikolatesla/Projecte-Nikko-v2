import React from "react";
import { Routes, Route } from "react-router-dom";
import Card from "./components/Card";
import Chat from "./components/Chat";
import Info from "./components/Info";

export default function App() {
  const page = {
    height: "100vh",
    width: "100vw",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial",
    background: 
    `
      radial-gradient(1200px 600px at 50% 0%, rgba(120, 150, 255, 0.12), transparent 70%),
      radial-gradient(1200px 600px at 50% 100%, rgba(200, 170, 255, 0.12), transparent 70%),
      linear-gradient(180deg, #f8faff 0%, #faf7ff 100%)
    `,

    margin: 0,
    overflow: "hidden",
  };

  return (
    <div style={page}>
      <Routes>
        <Route path="/" element={<Card />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/info" element={<Info />} />
      </Routes>
    </div>
  );
}

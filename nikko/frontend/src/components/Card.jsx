import React from "react";
import IconLock from "./IconLock";
import IconHeart from "./IconHeart";
import IconShield from "./IconShield";
import FeatureCard from "./FeatureCard";
import { useNavigate } from "react-router-dom";

export default function Card() {
  const navigate = useNavigate();

  const badgeStyle = {
    width: 80,
    height: 80,
    borderRadius: "70%",
    margin: "0 auto 16px",
    display: "grid",
    placeItems: "center",
    background: "linear-gradient(135deg, #8aa7ff 0%, #9d74ff 100%)",
    boxShadow: "0 10px 25px rgba(124, 58, 237, 0.2)",
  };

  return (
    <div
      style={{
        width: "min(420px, 92vw)",
        background: "#fff",
        borderRadius: 28,
        padding: "40px 32px 32px",
        boxShadow: "0 20px 60px rgba(30, 40, 70, 0.08)",
        textAlign: "center",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      {/* Estilos CSS locales modificados */}
      <style>{`
        .cssbuttons-io-button {
          background: linear-gradient(90deg, #3b82f6 0%, #a855f7 100%);
          color: white;
          font-family: inherit;
          padding: 0.35em;
          padding-left: 1.2em;
          font-size: 14px; /* CAMBIO: Letra más pequeña (antes 16px) */
          font-weight: 400;
          border-radius: 12px; /* CAMBIO: Bordes menos redondos (antes 999px) */
          border: none;
          letter-spacing: 0.05em;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
          overflow: hidden;
          position: relative;
          height: 3.2em;
          padding-right: 3.3em;
          cursor: pointer;
          width: 100%;
          margin-top: 10px;
        }

        .cssbuttons-io-button .icon {
          background: white;
          margin-left: 1em;
          position: absolute;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 2.4em; /* Ajuste proporcional */
          width: 2.4em;
          border-radius: 8px; /* CAMBIO: Ajustado para coincidir con el botón menos redondo */
          right: 0.4em;
          transition: all 0.3s;
        }

        .cssbuttons-io-button:hover .icon {
          width: calc(100% - 0.8em);
        }

        .cssbuttons-io-button .icon svg {
          width: 1.1em;
          transition: transform 0.3s;
          color: #a855f7;
        }

        .cssbuttons-io-button:hover .icon svg {
          transform: translateX(0.1em);
        }

        .cssbuttons-io-button:active .icon {
          transform: scale(0.95);
        }
      `}</style>

      {/* Icono Principal */}
      <div style={badgeStyle}>
        <IconShield size={40} color="white" />
      </div>

      <h1
        style={{
          margin: "12px 0 12px",
          fontSize: 26,
          fontWeight: 700,
          color: "#2a3a78",
          letterSpacing: "-0.5px",
        }}
      >
        No estás solo/a
      </h1>

      <p
        style={{
          margin: "0 auto 28px",
          maxWidth: "90%",
          fontSize: 16,
          lineHeight: 1.6,
          color: "#55628a",
        }}
      >
        Estoy aquí para escucharte. Este es un espacio seguro donde puedes
        compartir lo que sientes sin miedo ni juicio.
      </p>

      <div style={{ display: "grid", gap: 14, margin: "0 auto 24px" }}>
        <FeatureCard
          tone="blue"
          title="Confidencial"
          subtitle="Tus conversaciones son privadas y seguras"
          icon={<IconLock />}
        />
        <FeatureCard
          tone="purple"
          title="Apoyo empático"
          subtitle="Te acompaño con comprensión y sin juzgarte"
          icon={<IconHeart />}
        />
      </div>

      {/* Botón */}
      <button 
        className="cssbuttons-io-button" 
        onClick={() => navigate("/chat")}
        type="button"
      >
        Empezar conversación
        <div className="icon">
          <svg
            height="24"
            width="24"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M0 0h24v24H0z" fill="none"></path>
            <path
              d="M16.172 11l-5.364-5.364 1.414-1.414L20 12l-7.778 7.778-1.414-1.414L16.172 13H4v-2z"
              fill="currentColor"
            ></path>
          </svg>
        </div>
      </button>

      <div style={{ marginTop: 24, padding: "0 10px" }}>
        <p
          style={{
            fontSize: 11,
            lineHeight: 1.5,
            color: "#94a3b8",
            margin: 0,
          }}
        >
          Si estás en peligro inmediato, por favor contacta a un adulto de
          confianza o llama a servicios de emergencia
        </p>
      </div>
    </div>
  );
}
import React from "react";
import { useNavigate } from "react-router-dom";
import { 
  FaPhoneAlt, 
  FaRegCopy, 
  FaArrowLeft, 
  FaExclamationCircle, 
  FaShieldAlt, 
  FaHeart, 
  FaExternalLinkAlt 
} from "react-icons/fa"; 

import "../styles/info.css";

export default function Info() {
  const navigate = useNavigate();
  const goBack = () => navigate("/chat");

  return (
    <div className="infoPage">
      {/* HEADER */}
      <header className="infoTopBar">
        <button className="infoBackBtn" onClick={goBack}>
          <FaArrowLeft />
        </button>
        <div className="infoTopBarTitle">
          <h1>Recursos de Ayuda</h1>
          <p className="infoSubTitle">Contactos y consejos útiles</p>
        </div>
      </header>

      {/* CONTENIDO DESPLAZABLE */}
      <div className="infoContent">
        
        <div className="infoContainer">
            {/* ADVERTENCIA DE PELIGRO */}
            <section className="infoDangerAlert">
              <div className="alertIcon">
                <FaExclamationCircle />
              </div>
              <div className="alertText">
                <h3>¿Estás en peligro?</h3>
                <p>Si estás en una situación de riesgo inmediato, contacta a servicios de emergencia o a un adulto de confianza ahora mismo.</p>
              </div>
            </section>

            <h2 className="sectionTitle">Líneas de Ayuda</h2>

            {/* Tarjeta 1 */}
            <div className="infoCard">
              <div className="cardContent">
                <h3>Línea Nacional contra el Bullying</h3>
                <p>Atención 24/7 para situaciones de acoso escolar</p>
                <span className="phoneNumber">900 20 20 10</span>
              </div>
              <div className="cardActions">
                <button className="actionBtn outline"><FaRegCopy /></button>
                <button className="actionBtn primary"><FaPhoneAlt /></button>
              </div>
            </div>

            {/* Tarjeta 2 */}
            <div className="infoCard">
              <div className="cardContent">
                <h3>Teléfono ANAR</h3>
                <p>Ayuda a niños y adolescentes en riesgo</p>
                <span className="phoneNumber">900 20 20 10</span>
              </div>
              <div className="cardActions">
                <button className="actionBtn outline"><FaRegCopy /></button>
                <button className="actionBtn primary"><FaPhoneAlt /></button>
              </div>
            </div>

            {/* Tarjeta 3 Emergencias */}
            <div className="infoCard dangerCard">
              <div className="cardContent">
                <h3 className="dangerText">Emergencias</h3>
                <p>Para situaciones de peligro inmediato</p>
                <span className="phoneNumber dangerText">112</span>
              </div>
              <div className="cardActions">
                <button className="actionBtn outline"><FaRegCopy /></button>
                <button className="actionBtn danger"><FaPhoneAlt /></button>
              </div>
            </div>

            {/* CONSEJOS */}
            <div className="infoCard adviceCard">
              <div className="cardHeader">
                <div className="iconCircle blueIcon"><FaShieldAlt /></div>
                <h3>¿Qué hacer si sufro bullying?</h3>
              </div>
              <ul className="adviceList">
                <li>Habla con un adulto de confianza (padres, profesores, orientador)</li>
                <li>No respondas con violencia a la agresión</li>
                <li>Guarda evidencias (mensajes, capturas de pantalla)</li>
                <li>No estás solo/a, buscar ayuda es valentía, no debilidad</li>
              </ul>
            </div>

            {/* AYUDAR COMPAÑERO */}
            <div className="infoCard adviceCard">
              <div className="cardHeader">
                <div className="iconCircle heartIcon"><FaHeart /></div>
                <h3>Cómo ayudar a un compañero</h3>
              </div>
              <ul className="adviceList">
                <li>No participes ni apoyes el acoso</li>
                <li>Acompaña a la víctima y hazle saber que no está sola</li>
                <li>Reporta la situación a un adulto responsable</li>
                <li>Sé un ejemplo de respeto y empatía</li>
              </ul>
            </div>

            {/* RECURSOS ONLINE */}
            <div className="onlineResourcesContainer">
              <h2 className="sectionTitle">Recursos Online</h2>
              <a href="https://aepae.es/" target="_blank" rel="noopener noreferrer" className="resourceLink">
                <span>Fundación AEPAE</span>
                <FaExternalLinkAlt className="linkIcon" />
              </a>
              <a href="https://www.anar.org/" target="_blank" rel="noopener noreferrer" className="resourceLink">
                <span>Fundación ANAR</span>
                <FaExternalLinkAlt className="linkIcon" />
              </a>
            </div>

        </div>
      </div>
    </div>
  );
}

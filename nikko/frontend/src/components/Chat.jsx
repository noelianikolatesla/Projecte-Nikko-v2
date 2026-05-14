import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaBars } from "react-icons/fa";
import { IoSend } from "react-icons/io5";
import { cilVolumeHigh, cilMic, cilMediaStop } from "@coreui/icons";
import CIcon from "@coreui/icons-react";
import ReactMarkdown from "react-markdown";
import perfilChat from "../assets/perfil_chat.png";
import profilePic from "../assets/perfil_nikko.jpeg";
import profilePic2 from "../assets/perfil_user.png";
import LoadingAnimation from "../js/LoadingAnimation";

import "../styles/chat.css";

export default function Chat() {
  const navigate = useNavigate();
  
  // Refs existentes
  const sessionIdRef = useRef(crypto.randomUUID());
  const listRef = useRef(null);
  const isSendingRef = useRef(false);

  // Ref para controlar el objeto de Audio actual (para poder pausarlo)
  const currentAudioRef = useRef(null);

  // Variables de grabación
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Estado del chat
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // Estado para saber qué mensaje se está reproduciendo actualmente
  const [playingMessageId, setPlayingMessageId] = useState(null);

  const firstBotMessage = useMemo(
    () => ({
      id: crypto.randomUUID(),
      role: "bot",
      text: "Hola, me alegro de que estés aquí. Soy Nikko y estoy para escucharte. ¿Hay algo que te gustaría compartir conmigo?",
      timestamp: Date.now(),
    }),
    [],
  );

  const [messages, setMessages] = useState([firstBotMessage]);

  // Scroll automático
  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  // ==========================================
  // FUNCION CLAVE: ENVIAR TEXTO
  // ==========================================
  async function sendText(text) {
    const clean = (text || "").trim();

    if (!clean || isSendingRef.current) return;

    isSendingRef.current = true;
    setIsLoading(true);

    const userMsg = {
      id: crypto.randomUUID(),
      role: "user",
      text: clean, 
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput(""); 

    try {
      const res = await fetch("http://localhost:3001/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: clean,
          sessionId: sessionIdRef.current,
        }),
      });

      if (!res.ok) throw new Error("Error en la API");

      const data = await res.json();

      const botMsg = {
        id: crypto.randomUUID(),
        role: "bot",
        text: data.reply,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Error al conectar con la API:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "bot",
          text: "Lo siento, ahora mismo tengo un problema técnico, pero sigo aquí contigo 💙",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      isSendingRef.current = false;
      setIsLoading(false);
    }
  }

  // ====== ENVÍO MANUAL ======
  async function send() {
    await sendText(input);
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  // ====== FUNCIÓN TEXT TO SPEAK ========

  async function speak(text, messageId) {
    
    // 1. Si ya estamos reproduciendo ESTE mismo mensaje, lo paramos.
    if (playingMessageId === messageId) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0; // Reiniciar
      }
      setPlayingMessageId(null);
      return; // Salimos de la función
    }

    // 2. Si hay OTRO audio sonando, lo paramos antes de empezar el nuevo
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setPlayingMessageId(null);
    }

    try {
      console.log("🔊 Solicitando audio para:", text);
      
      // Marcamos este mensaje como "reproduciendo" (cargando)
      setPlayingMessageId(messageId); 

      const res = await fetch("http://localhost:3001/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) throw new Error("Error en la API de TTS");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      // Guardamos la referencia para poder pararlo luego
      currentAudioRef.current = audio;

      // Cuando el audio termine solo, reseteamos el estado
      audio.onended = () => {
        setPlayingMessageId(null);
        URL.revokeObjectURL(url);
        currentAudioRef.current = null;
      };

      audio.onerror = (e) => {
        console.error("❌ Error audio", e);
        setPlayingMessageId(null);
      };

      await audio.play();
    } catch (e) {
      console.error("❌ Error reproduciendo voz TTS", e);
      setPlayingMessageId(null);
    }
  }

  // ======= GRABACIÓN DE AUDIO (STT) ======
  async function startRecording() {
    // Si estamos reproduciendo audio del bot, lo paramos al empezar a grabar
    if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        setPlayingMessageId(null);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = sendAudio;

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setRecording(true);
    } catch (err) {
      console.error("Error al acceder al micrófono:", err);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  }

  async function sendAudio() {
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    
    const formData = new FormData();
    formData.append("audio", audioBlob);

    try {
      const res = await fetch("http://localhost:3001/api/stt", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Error en STT");

      const data = await res.json();
      
      if (data.text) {
        sendText(data.text);
      }
    } catch (error) {
      console.error("Error enviando audio:", error);
    }
  }

  const goBack = () => {
    navigate("/info");
  };

  const handleMainButton = () => {
    if (recording) {
      stopRecording();
    } else if (input.trim().length > 0) {
      send();
    } else {
      startRecording();
    }
  };

  const renderMainButtonIcon = () => {
    if (recording) return <CIcon icon={cilMediaStop} />;
    if (input.trim().length > 0) return <IoSend className="send-icon-svg" />;
    return <CIcon icon={cilMic} />;
  };

  return (
    <div className="chatPage">
      <header className="topBar">
        <div className="topBarLeft">
          <div className="topAvatar" aria-hidden="true">
            <img src={perfilChat} alt="Perfil" className="topAvatarImg" />
          </div>

          <div className="topBarText">
            <div className="topTitle">Nikko</div>
            <div className="topStatus">
              <span className="statusDot" />
              {isLoading ? "Escribiendo..." : "En línea"}
            </div>
          </div>
        </div>

        <button className="menuBtn" type="button" onClick={goBack}>
          <FaBars size={20} />
        </button>
      </header>

      <main className="chatBody" ref={listRef}>
        {messages.map((m) => (
          <div
            key={m.id}
            className={`msgRow ${m.role === "user" ? "right" : "left"}`}
          >
            {m.role === "bot" && (
              <div className="msgMiniIcon">
                <img src={profilePic} alt="Nikko" className="miniAvatar" />
              </div>
            )}

            <div className={`msgBubble ${m.role}`}>
              {m.role === "bot" && (
                <button
                  className="speakBtn"
                  onClick={() => speak(m.text, m.id)}
                  title={playingMessageId === m.id ? "Detener lectura" : "Escuchar respuesta"}
                  aria-label={playingMessageId === m.id ? "Detener lectura" : "Escuchar respuesta"}
                >
                  {playingMessageId === m.id ? (
                    <CIcon icon={cilMediaStop} />
                  ) : (
                    <CIcon icon={cilVolumeHigh} />
                  )}
                </button>
              )}

              {m.role === "bot" ? (
                <ReactMarkdown>{m.text}</ReactMarkdown>
              ) : (
                m.text 
              )}
              
              <div className="msgTime">
                {new Intl.DateTimeFormat("es-ES", {
                  hour: "2-digit",
                  minute: "2-digit",
                }).format(new Date(m.timestamp))}
              </div>
            </div>

            {m.role === "user" && (
              <div className="msgMiniIcon">
                <img src={profilePic2} alt="User" className="miniAvatar" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="msgRow left">
            <div className="msgMiniIcon">
              <img src={profilePic} alt="Nikko" className="miniAvatar" />
            </div>
            <div className="msgBubble bot">
              <LoadingAnimation />
            </div>
          </div>
        )}
      </main>

      <footer className="composerBar">
        <div className="composerInner">
          <div className="inputWrapper">
            <textarea
              className="chatInput"
              placeholder={
                recording ? "Grabando audio..." : "Escribe tu mensaje aquí..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              disabled={isLoading || recording} 
            />

            <button
              className={`sendBtn ${recording ? "recording" : ""}`}
              type="button"
              onClick={handleMainButton}
              disabled={isLoading && !recording}
              aria-label={
                recording
                  ? "Detener grabación"
                  : input.trim()
                    ? "Enviar mensaje"
                    : "Grabar audio"
              }
            >
              {renderMainButtonIcon()}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
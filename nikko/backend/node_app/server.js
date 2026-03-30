import "dotenv/config";

import express from "express";
import cors from "cors";
import agentPkg from "@aws-sdk/client-bedrock-agent-runtime";

const { BedrockAgentRuntimeClient, InvokeAgentCommand } = agentPkg;

const app = express();
app.use(cors());
app.use(express.json());

const client = new BedrockAgentRuntimeClient({
  region: process.env.AWS_REGION,
});

app.get("/", (req, res) => {
  res.json({ status: "ok" });
});

app.post("/api/chat", async (req, res) => {
  console.log("📩 Mensaje recibido:", req.body);
  const { message, sessionId } = req.body;

  if (!message || !sessionId) {
    return res.status(400).json({
      reply: "Faltan datos para procesar el mensaje.",
    });
  }

  try {
    const command = new InvokeAgentCommand({
      agentId: process.env.BEDROCK_AGENT_ID,
      agentAliasId: process.env.BEDROCK_ALIAS_ID,
      sessionId,
      inputText: message,
    });

    const response = await client.send(command);

    let output = "";

    for await (const event of response.completion) {
      if (event.chunk?.bytes) {
        output += new TextDecoder().decode(event.chunk.bytes);
      }
    }

    res.json({ reply: output || "Estoy aquí contigo 💙" });
  } catch (error) {
    console.error("❌ Error Bedrock:", error);
    res.status(500).json({
      reply:
        "Lo siento, ahora mismo tengo un problema técnico, pero sigo aquí contigo 💙",
    });
  }
});

app.listen(3001, () => {
  console.log("✅ Backend activo en http://localhost:3001");
});



const statusEl = document.querySelector("#status");
const timeline = document.querySelector("#timeline");
const recordButton = document.querySelector("#recordButton");
const textForm = document.querySelector("#textForm");
const textInput = document.querySelector("#textInput");

const sessionId = crypto.randomUUID();
const wsProtocol = location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(`${wsProtocol}://${location.host}/ws/session/${sessionId}`);

let mediaRecorder = null;
let chunks = [];
let currentAssistantMessage = null;

function setStatus(text, state = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${state}`.trim();
}

function addMessage(kind, text = "") {
  const node = document.createElement("div");
  node.className = `message ${kind}`;
  node.textContent = text;
  timeline.appendChild(node);
  timeline.scrollTop = timeline.scrollHeight;
  return node;
}

function sendJson(payload) {
  socket.send(JSON.stringify(payload));
}

socket.addEventListener("open", () => {
  setStatus("Conectado", "ready");
});

socket.addEventListener("close", () => {
  setStatus("Desconectado", "error");
});

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "session.ready") {
    addMessage("system", `Sesion ${data.session_id} lista. Graba audio o envia texto.`);
  }

  if (data.type === "transcription.started") {
    addMessage("system", "Transcribiendo audio...");
  }

  if (data.type === "transcription.completed") {
    addMessage("user", data.text);
  }

  if (data.type === "ai.response.started") {
    currentAssistantMessage = addMessage("assistant", "");
  }

  if (data.type === "ai.response.delta" && currentAssistantMessage) {
    currentAssistantMessage.textContent += data.text;
    timeline.scrollTop = timeline.scrollHeight;
  }

  if (data.type === "ai.response.completed") {
    currentAssistantMessage = null;
  }

  if (data.type === "tts.started") {
    addMessage("system", "Generando audio de respuesta...");
  }

  if (data.type === "tts.completed") {
    const audio = new Audio(`data:${data.mime_type};base64,${data.audio}`);
    audio.play();
    addMessage("system", "Audio reproducido desde TTS local.");
  }

  if (data.type === "error") {
    addMessage("error", data.message);
    setStatus("Error", "error");
  }
});

recordButton.addEventListener("click", async () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    recordButton.textContent = "Grabar";
    recordButton.classList.remove("recording");
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : "audio/webm";

  chunks = [];
  mediaRecorder = new MediaRecorder(stream, { mimeType });

  mediaRecorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) {
      chunks.push(event.data);
    }
  });

  mediaRecorder.addEventListener("stop", async () => {
    stream.getTracks().forEach((track) => track.stop());

    const blob = new Blob(chunks, { type: mimeType });
    const buffer = await blob.arrayBuffer();

    addMessage("system", `Enviando ${(blob.size / 1024).toFixed(1)} KB de audio...`);
    sendJson({ type: "start_utterance", mime_type: mimeType });
    socket.send(buffer);
    sendJson({ type: "end_utterance" });
  });

  mediaRecorder.start();
  recordButton.textContent = "Detener";
  recordButton.classList.add("recording");
});

textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = textInput.value.trim();
  if (!text) {
    return;
  }

  addMessage("user", text);
  sendJson({ type: "text_message", text });
  textInput.value = "";
});

const statusEl = document.querySelector("#status");
const timeline = document.querySelector("#timeline");
const diagnosticsTimeline = document.querySelector("#diagnosticsTimeline");
const recordButton = document.querySelector("#recordButton");
const textForm = document.querySelector("#textForm");
const textInput = document.querySelector("#textInput");
const promptButtons = document.querySelectorAll("[data-prompt]");

const sessionId = crypto.randomUUID();
const wsProtocol = location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(`${wsProtocol}://${location.host}/ws/session/${sessionId}`);

let mediaRecorder = null;
let activeStream = null;
let vadContext = null;
let vadTimer = null;
let currentAssistantMessage = null;
const audioQueue = [];
let isPlayingAudio = false;

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

function addDiagnostic(text = "") {
  if (!diagnosticsTimeline) {
    return;
  }

  const node = document.createElement("div");
  node.className = "diagnostic-entry";
  node.textContent = text;
  diagnosticsTimeline.appendChild(node);
  diagnosticsTimeline.scrollTop = diagnosticsTimeline.scrollHeight;
}

function sendJson(payload) {
  socket.send(JSON.stringify(payload));
}

socket.addEventListener("open", () => {
  setStatus("Conectado", "ready");
  addMessage(
    "system",
    "Demo lista. Esta UI presenta el stack, la arquitectura y tambien permite probar el workflow de voz en tiempo real."
  );
});

socket.addEventListener("close", () => {
  setStatus("Desconectado", "error");
});

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "session.ready") {
    addMessage("system", `Sesion ${data.session_id} lista. Graba audio o envia texto.`);
    addDiagnostic(`Sesion ${data.session_id} lista.`);
  }

  if (data.type === "transcription.started") {
    addMessage("system", "Transcribiendo audio...");
    addDiagnostic("Inicio de transcripcion.");
  }

  if (data.type === "transcription.partial") {
    addDiagnostic(`Parcial STT: ${data.text}`);
  }

  if (data.type === "transcription.completed") {
    addMessage("user", data.text);
    addDiagnostic(`Transcripcion final: ${data.text}`);
  }

  if (data.type === "ai.response.started") {
    currentAssistantMessage = addMessage("assistant", "");
  }

  if (data.type === "ai.response.delta" && currentAssistantMessage) {
    currentAssistantMessage.textContent += data.text;
    timeline.scrollTop = timeline.scrollHeight;
  }

  if (data.type === "ai.response.completed") {
    addDiagnostic("Streaming LLM completado.");
    currentAssistantMessage = null;
  }

  if (data.type === "tts.started") {
    addDiagnostic(`Generando audio segmento ${data.segment}...`);
  }

  if (data.type === "tts.segment.completed") {
    addDiagnostic(`Segmento TTS ${data.segment ?? "?"} listo para reproducir.`);
    queueAudio(data.mime_type, data.audio);
  }

  if (data.type === "tts.completed") {
    addDiagnostic(`TTS completado en ${data.segments} segmento(s).`);
  }

  if (data.type === "metrics") {
    addDiagnostic(`Metricas: ${JSON.stringify(data.metrics)}`);
  }

  if (data.type === "error") {
    addMessage("error", data.message);
    addDiagnostic(`Error: ${data.message}`);
    setStatus("Error", "error");
  }
});

function queueAudio(mimeType, base64Audio) {
  audioQueue.push(`data:${mimeType};base64,${base64Audio}`);
  playNextAudio();
}

function playNextAudio() {
  if (isPlayingAudio || audioQueue.length === 0) {
    return;
  }

  isPlayingAudio = true;
  const audio = new Audio(audioQueue.shift());
  audio.addEventListener("ended", () => {
    isPlayingAudio = false;
    playNextAudio();
  });
  audio.play();
}

function stopRecording() {
  if (!mediaRecorder || mediaRecorder.state !== "recording") {
    return;
  }

  mediaRecorder.stop();
  recordButton.textContent = "Grabar";
  recordButton.classList.remove("recording");
}

function startVad(stream) {
  vadContext = new AudioContext();
  const source = vadContext.createMediaStreamSource(stream);
  const analyser = vadContext.createAnalyser();
  const samples = new Uint8Array(analyser.fftSize);
  let silentFrames = 0;

  source.connect(analyser);

  vadTimer = window.setInterval(() => {
    analyser.getByteTimeDomainData(samples);
    const average = samples.reduce((sum, value) => sum + Math.abs(value - 128), 0) / samples.length;

    if (average < 3.5) {
      silentFrames += 1;
    } else {
      silentFrames = 0;
    }

    if (silentFrames > 18 && mediaRecorder?.state === "recording") {
      addDiagnostic("Silencio detectado, cerrando utterance...");
      stopRecording();
    }
  }, 100);
}

function stopVad() {
  if (vadTimer) {
    window.clearInterval(vadTimer);
    vadTimer = null;
  }
  if (vadContext) {
    vadContext.close();
    vadContext = null;
  }
}

recordButton.addEventListener("click", async () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
    return;
  }

  activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : "audio/webm";

  mediaRecorder = new MediaRecorder(activeStream, { mimeType });
  sendJson({ type: "start_utterance", mime_type: mimeType });

  mediaRecorder.addEventListener("dataavailable", async (event) => {
    if (event.data.size > 0) {
      socket.send(await event.data.arrayBuffer());
    }
  });

  mediaRecorder.addEventListener("stop", () => {
    activeStream.getTracks().forEach((track) => track.stop());
    stopVad();
    addDiagnostic("Procesando utterance...");
    sendJson({ type: "end_utterance" });
  });

  mediaRecorder.start(750);
  startVad(activeStream);
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

promptButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const prompt = button.dataset.prompt;
    textInput.value = prompt;
    textInput.focus();
  });
});

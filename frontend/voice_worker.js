(function () {
  const parentWindow = window.parent;
  const rootDoc = parentWindow.document;
  const backendUrlEl = rootDoc.getElementById("va-backend-url");
  const BACKEND = backendUrlEl ? backendUrlEl.textContent.trim() : "http://localhost:8000";
  const root = rootDoc.getElementById("voiceagent-ui-root");
  if (!root) return;

  if (parentWindow.__voiceAgentController && typeof parentWindow.__voiceAgentController.destroy === "function") {
    try { parentWindow.__voiceAgentController.destroy(); } catch (e) {}
  }

  const fab = rootDoc.getElementById("voiceagent-fab");
  const indicator = rootDoc.getElementById("voiceagent-indicator");
  const debugBox = rootDoc.getElementById("voiceagent-debug");
  const overlay = rootDoc.getElementById("voiceagent-overlay");
  const closeBtn = rootDoc.getElementById("voiceagent-close");
  const overlayText = rootDoc.getElementById("voiceagent-text");
  const overlaySubtext = rootDoc.getElementById("voiceagent-subtext");
  const conversation = rootDoc.getElementById("voiceagent-conversation");

  let voiceEnabled = false;
  let overlayActive = false;
  let speaking = false;
  let permissionDenied = false;
  let wakeWordTriggered = false;
  let mediaStreamRef = null;
  let wakeRecorder = null;
  let wakeFallbackActive = false;
  let wakeFallbackInFlight = false;
  let audioChunks = [];
  let queryRecorder = null;
  let queryStream = null;
  let querySilenceTimer = null;
  let queryStopTimer = null;
  let debugState = "off";
  let debugSource = "none";
  let debugHeard = "-";
  let debugTranscribe = "-";
  let debugError = "-";
  let conversationTurns = [];
  let thinkingMessageId = null;

  function renderDebug() {
    if (!debugBox) return;
    debugBox.style.display = voiceEnabled ? "block" : "none";
    debugBox.innerHTML = `<strong>Voice Debug</strong>\nState: ${debugState}\nSource: ${debugSource}\nLast heard: ${debugHeard}\nLast transcribe: ${debugTranscribe}\nLast error: ${debugError}`;
  }
  function setDebugState(state) { debugState = state; renderDebug(); }
  function setDebugSource(source) { debugSource = source; renderDebug(); }
  function setDebugHeard(text) { debugHeard = text && String(text).trim() ? String(text).trim() : "-"; renderDebug(); }
  function setDebugTranscribe(text) { debugTranscribe = text && String(text).trim() ? String(text).trim() : "-"; renderDebug(); }
  function setDebugError(text) { debugError = text && String(text).trim() ? String(text).trim() : "-"; renderDebug(); }

  function setOverlayState(state) {
    overlay.classList.remove("listening", "thinking", "speaking");
    if (state) overlay.classList.add(state);
  }
  function setOverlayText(title, subtitle) {
    overlayText.textContent = title;
    overlaySubtext.textContent = subtitle || "";
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderConversation() {
    if (!conversation) return;
    if (!overlayActive || conversationTurns.length === 0) {
      conversation.classList.remove("active");
      conversation.innerHTML = "";
      return;
    }
    conversation.classList.add("active");
    conversation.innerHTML = conversationTurns.map((turn) => {
      const side = turn.role === "user" ? "user" : "agent";
      const label = turn.role === "user" ? "You" : "VoiceAgent";
      const thinkingClass = turn.state === "thinking" ? " thinking" : "";
      return `<div class="voiceagent-message-row ${side}">
        <div class="voiceagent-message ${side}${thinkingClass}">
          <span class="voiceagent-message-label">${label}</span>
          <div class="voiceagent-message-text">${escapeHtml(turn.text)}</div>
        </div>
      </div>`;
    }).join("");
    conversation.scrollTop = conversation.scrollHeight;
  }

  function addConversationTurn(role, text, state) {
    const turn = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      role: role,
      text: text,
      state: state || "final",
    };
    conversationTurns.push(turn);
    renderConversation();
    return turn.id;
  }

  function updateConversationTurn(turnId, text, state) {
    if (!turnId) return;
    const target = conversationTurns.find((turn) => turn.id === turnId);
    if (!target) return;
    target.text = text;
    target.state = state || target.state;
    renderConversation();
  }

  function clearConversation() {
    conversationTurns = [];
    thinkingMessageId = null;
    renderConversation();
  }

  function cleanupQuery() {
    if (querySilenceTimer) {
      clearTimeout(querySilenceTimer);
      querySilenceTimer = null;
    }
    if (queryStopTimer) {
      clearTimeout(queryStopTimer);
      queryStopTimer = null;
    }
    if (queryRecorder) {
      try { queryRecorder.ondataavailable = null; queryRecorder.onstop = null; queryRecorder.onerror = null; } catch (e) {}
      try { if (queryRecorder.state !== "inactive") queryRecorder.stop(); } catch (e) {}
    }
    queryRecorder = null;
    if (queryStream) {
      try { queryStream.getTracks().forEach(track => track.stop()); } catch (e) {}
    }
    queryStream = null;
  }

  function stopWakeFallback() {
    wakeFallbackActive = false;
    audioChunks = [];
    if (wakeRecorder) {
      try { wakeRecorder.ondataavailable = null; wakeRecorder.onstop = null; wakeRecorder.onerror = null; } catch (e) {}
      try { if (wakeRecorder.state !== "inactive") wakeRecorder.stop(); } catch (e) {}
    }
    wakeRecorder = null;
  }

  async function requestMicrophoneAccess() {
    try {
      setDebugState("requesting-mic");
      const stream = await parentWindow.navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      mediaStreamRef = stream;
      permissionDenied = false;
      setDebugState("mic-ready");
      setDebugError("-");
      return true;
    } catch (error) {
      permissionDenied = true;
      indicator.style.display = "inline-flex";
      indicator.textContent = "Microphone permission denied";
      setDebugState("error");
      setDebugError(`mic-permission: ${error && error.message ? error.message : error}`);
      return false;
    }
  }

  function speak(text, onEnd) {
    parentWindow.speechSynthesis.cancel();
    speaking = true;
    setDebugState("speaking");
    setOverlayState("speaking");
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = function () {
      speaking = false;
      if (typeof onEnd === "function") onEnd();
    };
    utterance.onerror = function () {
      speaking = false;
      if (typeof onEnd === "function") onEnd();
    };
    parentWindow.speechSynthesis.speak(utterance);
  }

  function deactivateOverlay(resumeWake) {
    overlayActive = false;
    wakeWordTriggered = false;
    cleanupQuery();
    setOverlayState("");
    overlay.classList.remove("active");
    parentWindow.speechSynthesis.cancel();
    renderConversation();
    if (voiceEnabled && resumeWake) {
      setTimeout(() => startWakeFallback(), 300);
    }
  }

  async function listenForQuery() {
    if (!voiceEnabled || !overlayActive) return;
    cleanupQuery();
    setDebugSource("query-whisper");
    setDebugState("active-listening");
    setOverlayState("listening");
    setOverlayText("Listening...", "Ask about fares, vendors, payment behavior, or demand.");
    let queryChunks = [];
    let hasAudio = false;
    try {
      queryStream = await parentWindow.navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      let recorderOptions = undefined;
      if (parentWindow.MediaRecorder.isTypeSupported) {
        if (parentWindow.MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          recorderOptions = { mimeType: "audio/webm;codecs=opus", audioBitsPerSecond: 128000 };
        } else if (parentWindow.MediaRecorder.isTypeSupported("audio/webm")) {
          recorderOptions = { mimeType: "audio/webm", audioBitsPerSecond: 128000 };
        }
      }
      queryRecorder = recorderOptions
        ? new parentWindow.MediaRecorder(queryStream, recorderOptions)
        : new parentWindow.MediaRecorder(queryStream);
      queryRecorder.ondataavailable = function (event) {
        if (event.data && event.data.size > 0) {
          queryChunks.push(event.data);
          hasAudio = true;
          if (querySilenceTimer) clearTimeout(querySilenceTimer);
          querySilenceTimer = setTimeout(() => {
            if (queryRecorder && queryRecorder.state === "recording") queryRecorder.stop();
          }, 1800);
        }
      };
      queryRecorder.onstop = async function () {
        if (queryStream) {
          try { queryStream.getTracks().forEach(track => track.stop()); } catch (e) {}
        }
        queryStream = null;
        if (!voiceEnabled || !overlayActive) return;
        if (!hasAudio || queryChunks.length === 0) {
          setDebugState("error");
          setOverlayText("I didn't catch that.", "Try speaking again.");
          setTimeout(() => { if (voiceEnabled && overlayActive) listenForQuery(); }, 1000);
          return;
        }
        const blob = new Blob(queryChunks, { type: "audio/webm" });
        if (blob.size < 500) {
          setDebugState("error");
          setOverlayText("I didn't catch that.", "Try speaking again.");
          setTimeout(() => { if (voiceEnabled && overlayActive) listenForQuery(); }, 1000);
          return;
        }
        setDebugState("thinking");
        setOverlayState("thinking");
        setOverlayText("Thinking...", "Hold on while I work through that.");
        try {
          const formData = new FormData();
          formData.append("audio", new File([blob], "query.webm", { type: "audio/webm" }));
          formData.append("mode", "query");
          const transcribeRes = await parentWindow.fetch(BACKEND + "/transcribe", { method: "POST", body: formData });
          const transcribeData = await transcribeRes.json();
          const transcript = (transcribeData.text || "").trim();
          if (!transcript) {
            setDebugState("error");
            setOverlayText("I didn't catch that.", "Try speaking again.");
            setTimeout(() => { if (voiceEnabled && overlayActive) listenForQuery(); }, 1000);
            return;
          }
          setDebugHeard(transcript);
          setDebugTranscribe(transcript);
          addConversationTurn("user", transcript);
          if (transcript.toLowerCase().includes("stop")) {
            deactivateOverlay(true);
            return;
          }
          thinkingMessageId = addConversationTurn("agent", "Thinking...", "thinking");
          setOverlayText("Thinking...", "Working on an answer for you.");
          const askRes = await parentWindow.fetch(BACKEND + "/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: transcript, voice_speed: 1.0 })
          });
          const askData = await askRes.json();
          const answer = askData.answer || "I couldn't find an answer.";
          updateConversationTurn(thinkingMessageId, answer, "final");
          thinkingMessageId = null;
          setOverlayText(answer, 'Say another question, or say "stop" to exit.');
          setDebugError("-");
          speak(answer, () => {
            if (voiceEnabled && overlayActive) listenForQuery();
          });
        } catch (error) {
          setDebugState("error");
          setDebugError(`query: ${error && error.message ? error.message : error}`);
          updateConversationTurn(thinkingMessageId, "Connection issue. Check the backend is running.", "final");
          thinkingMessageId = null;
          setOverlayText("Connection issue.", "Check the backend is running.");
          setTimeout(() => { if (voiceEnabled && overlayActive) listenForQuery(); }, 1500);
        }
      };
      queryRecorder.onerror = function (event) {
        setDebugState("error");
        setDebugError(`query-recorder: ${event && event.error ? event.error : "unknown"}`);
        setTimeout(() => { if (voiceEnabled && overlayActive) listenForQuery(); }, 1000);
      };
      queryRecorder.start(500);
      queryStopTimer = setTimeout(() => {
        if (queryRecorder && queryRecorder.state === "recording") queryRecorder.stop();
      }, 12000);
    } catch (error) {
      setDebugState("error");
      setDebugError(`query-mic: ${error && error.message ? error.message : error}`);
      setOverlayText("Microphone error.", "Please check permissions.");
    }
  }

  function activateOverlay() {
    overlayActive = true;
    wakeWordTriggered = true;
    stopWakeFallback();
    overlay.classList.add("active");
    setDebugState("speaking");
    setOverlayState("speaking");
    if (conversationTurns.length === 0) {
      addConversationTurn("agent", "Hey, how can I help you today?");
    }
    renderConversation();
    setOverlayText("Hey, how can I help you today?", "Ask about NYC taxi trips, fares, vendors, or demand patterns.");
    speak("Hey, how can I help you today?", () => {
      if (voiceEnabled && overlayActive) listenForQuery();
    });
  }

  async function processWakeBlob(blob) {
    if (!voiceEnabled || overlayActive || wakeFallbackInFlight || !blob || blob.size < 500) return;
    wakeFallbackInFlight = true;
    setDebugSource("backend-whisper");
    setDebugState("wake-transcribing");
    try {
      const formData = new FormData();
      formData.append("audio", new File([blob], "wake.webm", { type: blob.type || "audio/webm" }));
      formData.append("mode", "wake");
      const response = await parentWindow.fetch(BACKEND + "/transcribe", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      const transcript = (data.text || "").trim().toLowerCase();
      if (transcript) {
        setDebugHeard(transcript);
        setDebugTranscribe(transcript);
      }
      if (!wakeWordTriggered && transcript.includes("hey agent")) {
        activateOverlay();
      } else if (!overlayActive && voiceEnabled) {
        setDebugState("wake-listening");
      }
    } catch (error) {
      setDebugState("error");
      setDebugError(`fallback: ${error && error.message ? error.message : error}`);
    } finally {
      wakeFallbackInFlight = false;
    }
  }

  function startWakeFallback() {
    if (!voiceEnabled || overlayActive || permissionDenied) return;
    stopWakeFallback();
    audioChunks = [];
    wakeFallbackActive = true;
    setDebugSource("backend-whisper");
    setDebugState("wake-listening");
    if (!parentWindow.MediaRecorder || !mediaStreamRef) {
      indicator.style.display = "inline-flex";
      indicator.textContent = "Wake word requires MediaRecorder";
      setDebugState("error");
      setDebugError("fallback: MediaRecorder unavailable");
      return;
    }
    let recorderOptions = undefined;
    if (parentWindow.MediaRecorder.isTypeSupported) {
      if (parentWindow.MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        recorderOptions = { mimeType: "audio/webm;codecs=opus", audioBitsPerSecond: 128000 };
      } else if (parentWindow.MediaRecorder.isTypeSupported("audio/webm")) {
        recorderOptions = { mimeType: "audio/webm", audioBitsPerSecond: 128000 };
      }
    }
    try {
      wakeRecorder = recorderOptions
        ? new parentWindow.MediaRecorder(mediaStreamRef, recorderOptions)
        : new parentWindow.MediaRecorder(mediaStreamRef);
    } catch (error) {
      setDebugState("error");
      setDebugError(`fallback-init: ${error && error.message ? error.message : error}`);
      return;
    }
    wakeRecorder.ondataavailable = function (event) {
      if (!wakeFallbackActive || !event.data || event.data.size === 0) return;
      audioChunks.push(event.data);
      if (audioChunks.length > 4) audioChunks.shift();
      const combinedBlob = new Blob(audioChunks, { type: event.data.type || "audio/webm" });
      processWakeBlob(combinedBlob);
    };
    wakeRecorder.onerror = function (event) {
      setDebugState("error");
      setDebugError(`recorder: ${event && event.error ? event.error.name || event.error.message : "unknown"}`);
    };
    wakeRecorder.onstop = function () {
      if (voiceEnabled && !overlayActive && wakeFallbackActive) {
        setTimeout(() => startWakeFallback(), 300);
      }
    };
    try {
      wakeRecorder.start(3000);
      indicator.style.display = "inline-flex";
      indicator.textContent = "Voice Active (Say 'Hey Agent')";
      setDebugError("-");
    } catch (error) {
      setDebugState("error");
      setDebugError(`fallback-start: ${error && error.message ? error.message : error}`);
    }
  }

  async function enableVoiceMode() {
    voiceEnabled = true;
    permissionDenied = false;
    clearConversation();
    fab.textContent = "Voice Mode On";
    indicator.style.display = "inline-flex";
    if (debugBox) debugBox.style.display = "block";
    const allowed = await requestMicrophoneAccess();
    if (!allowed) {
      voiceEnabled = false;
      fab.textContent = "Enable Voice Mode";
      if (debugBox) debugBox.style.display = "none";
      return;
    }
    indicator.textContent = "Voice Active (Say 'Hey Agent')";
    startWakeFallback();
  }

  function disableVoiceMode() {
    voiceEnabled = false;
    overlayActive = false;
    speaking = false;
    permissionDenied = false;
    wakeWordTriggered = false;
    parentWindow.speechSynthesis.cancel();
    cleanupQuery();
    stopWakeFallback();
    if (mediaStreamRef) {
      try { mediaStreamRef.getTracks().forEach(track => track.stop()); } catch (e) {}
      mediaStreamRef = null;
    }
    fab.textContent = "Enable Voice Mode";
    indicator.style.display = "none";
    if (debugBox) debugBox.style.display = "none";
    overlay.classList.remove("active", "listening", "thinking", "speaking");
    setOverlayText('Say "Hey Agent" to start a conversation.', "The dashboard stays visible underneath while the assistant listens on top.");
    clearConversation();
    debugState = "off";
    debugSource = "none";
    debugHeard = "-";
    debugTranscribe = "-";
    debugError = "-";
    renderDebug();
  }

  function onFabClick() {
    if (voiceEnabled) disableVoiceMode();
    else enableVoiceMode();
  }
  function onCloseClick() {
    deactivateOverlay(true);
  }

  fab.addEventListener("click", onFabClick);
  closeBtn.addEventListener("click", onCloseClick);
  renderDebug();
  if (debugBox) debugBox.style.display = "none";

  parentWindow.__voiceAgentController = {
    destroy() {
      fab.removeEventListener("click", onFabClick);
      closeBtn.removeEventListener("click", onCloseClick);
      disableVoiceMode();
    }
  };
})();

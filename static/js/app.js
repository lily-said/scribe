/**
 * Scribe — Gemini Smart Glasses I/O Prototype
 * Frontend Controller (Unified Voice-Driven, Mode-Free Architecture)
 */

class SmartGlassesApp {
  constructor() {
    this.mediaStream = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.isProcessing = false;
    this.lastAudioUrl = null;
    this.lastSpokenText = "";
    this.currentCapturedImage = null;

    // Audio Visualizer Context
    this.visualizerAnimationId = null;

    // Elements
    this.video = document.getElementById('camera-feed');
    this.canvas = document.getElementById('preview-canvas');
    this.hudWaveform = document.getElementById('hud-waveform');
    this.audioPlayer = document.getElementById('audio-player');
    this.mainActionBtn = document.getElementById('main-action-btn');
    this.actionText = document.getElementById('action-text');
    this.actionIcon = document.getElementById('action-icon');
    this.hudTranscript = document.getElementById('hud-transcript');
    this.hudStatusBadge = document.getElementById('hud-status-badge');
    this.hudVisionStatus = document.getElementById('hud-vision-status');
    this.audioStatusLabel = document.getElementById('audio-status-label');
    this.latencyDisplay = document.getElementById('latency-display');
    this.connectionDot = document.getElementById('connection-status-dot');
    this.connectionText = document.getElementById('connection-status-text');

    // Shutter & Snapshot Preview Elements
    this.shutterFlash = document.getElementById('shutter-flash');
    this.snapshotPip = document.getElementById('snapshot-preview-pip');
    this.snapshotPipImg = document.getElementById('snapshot-pip-img');
    this.captureTimingSelect = document.getElementById('capture-timing-select');
    this.captureTiming = localStorage.getItem('gemini_capture_timing') || 'start';

    // Dialogue & Inspector Elements
    this.spokenDisplay = document.getElementById('speech-spoken-display');
    this.ttsBadge = document.getElementById('tts-source-badge');
    this.replayBtn = document.getElementById('replay-audio-btn');
    this.wearerQueryDisplay = document.getElementById('wearer-query-display');
    this.aiResponseDisplay = document.getElementById('ai-response-display');
    this.detectedIntentBadge = document.getElementById('detected-intent-badge');
    this.visualTagsContainer = document.getElementById('visual-tags-container');
    this.extraDetailsContainer = document.getElementById('extra-details-container');
    this.extraDetailsText = document.getElementById('extra-details-text');

    // Cancel & Speed Controls
    this.cancelBtn = document.getElementById('cancel-action-btn');
    this.fastModeCheckbox = document.getElementById('fast-mode-checkbox');
    this.currentAbortController = null;

    // Input elements
    this.customPromptInput = document.getElementById('user-custom-prompt');
    this.sendTextBtn = document.getElementById('send-text-btn');

    // Settings
    this.apiKeyInput = document.getElementById('api-key-input');
    this.voiceSelect = document.getElementById('voice-select');
    this.cameraSelect = document.getElementById('camera-select');
    this.settingsModal = document.getElementById('settings-modal');

    this.init();
  }

  async init() {
    this.loadSettings();
    this.setupEventListeners();
    await this.initCamera();
    this.initAudioVisualizer();
    this.checkHealth();
  }

  loadSettings() {
    const savedKey = localStorage.getItem('gemini_api_key') || '';
    const savedVoice = localStorage.getItem('gemini_voice') || 'Kore';
    const savedTiming = localStorage.getItem('gemini_capture_timing') || 'start';
    if (this.apiKeyInput) this.apiKeyInput.value = savedKey;
    if (this.voiceSelect) this.voiceSelect.value = savedVoice;
    if (this.captureTimingSelect) this.captureTimingSelect.value = savedTiming;
    this.captureTiming = savedTiming;
  }

  saveSettings() {
    if (this.apiKeyInput) {
      localStorage.setItem('gemini_api_key', this.apiKeyInput.value.trim());
    }
    if (this.voiceSelect) {
      localStorage.setItem('gemini_voice', this.voiceSelect.value);
    }
    if (this.captureTimingSelect) {
      localStorage.setItem('gemini_capture_timing', this.captureTimingSelect.value);
      this.captureTiming = this.captureTimingSelect.value;
    }
    if (this.settingsModal) {
      this.settingsModal.classList.remove('open');
    }
    this.checkHealth();
  }

  getApiKey() {
    return localStorage.getItem('gemini_api_key') || '';
  }

  getVoice() {
    return localStorage.getItem('gemini_voice') || 'Kore';
  }

  async checkHealth() {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      const hasKey = data.has_api_key || !!this.getApiKey();
      if (hasKey) {
        this.connectionDot.style.backgroundColor = 'var(--accent-green)';
        this.connectionDot.style.boxShadow = '0 0 8px var(--accent-green)';
        this.connectionText.textContent = `Connected (${data.vision_model})`;
      } else {
        this.connectionDot.style.backgroundColor = 'var(--accent-amber)';
        this.connectionDot.style.boxShadow = '0 0 8px var(--accent-amber)';
        this.connectionText.textContent = 'API Key Required (Open Settings)';
      }
    } catch (e) {
      this.connectionDot.style.backgroundColor = 'var(--accent-red)';
      this.connectionText.textContent = 'Backend Offline';
    }
  }

  async initCamera(deviceId = null) {
    try {
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop());
      }

      const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'environment', width: { ideal: 1280 } },
        audio: true
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.mediaStream;
      this.video.play();

      // Populate camera device list
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === 'videoinput');
      this.cameraSelect.innerHTML = '<option value="">Default Web Camera</option>';
      videoDevices.forEach((dev, idx) => {
        const opt = document.createElement('option');
        opt.value = dev.deviceId;
        opt.textContent = dev.label || `Camera ${idx + 1}`;
        if (deviceId && dev.deviceId === deviceId) opt.selected = true;
        this.cameraSelect.appendChild(opt);
      });

    } catch (err) {
      console.warn('Camera access denied or unavailable:', err);
      this.hudVisionStatus.textContent = 'CAMERA OFFLINE (USING PRESETS)';
      this.drawPlaceholderVideo();
    }
  }

  drawPlaceholderVideo() {
    const ctx = this.canvas.getContext('2d');
    this.canvas.width = 640;
    this.canvas.height = 400;
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, 640, 400);
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.2)';
    ctx.lineWidth = 1;
    for (let x = 0; x < 640; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 400);
      ctx.stroke();
    }
    for (let y = 0; y < 400; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(640, y);
      ctx.stroke();
    }
    ctx.fillStyle = '#00f2fe';
    ctx.font = '16px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('CAMERA STANDBY — TAP A DEMO SCENARIO BELOW', 320, 200);
  }

  initAudioVisualizer() {
    const canvas = this.hudWaveform;
    const ctx = canvas.getContext('2d');
    let phase = 0;

    const renderWaveform = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2;

      if (this.isRecording || (this.audioPlayer && !this.audioPlayer.paused)) {
        ctx.strokeStyle = this.isRecording ? '#ef4444' : '#00f2fe';
        ctx.beginPath();
        const sliceWidth = canvas.width / 20;
        let x = 0;
        for (let i = 0; i <= 20; i++) {
          const v = Math.sin(phase + i * 0.5) * 12 + Math.cos(phase * 1.5 + i * 0.3) * 4;
          const y = canvas.height / 2 + v;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
          x += sliceWidth;
        }
        ctx.stroke();
        phase += 0.2;
      } else {
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.3)';
        ctx.beginPath();
        ctx.moveTo(0, canvas.height / 2);
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
      }

      this.visualizerAnimationId = requestAnimationFrame(renderWaveform);
    };

    renderWaveform();
  }

  setupEventListeners() {
    // Push-to-Talk Action Button
    this.mainActionBtn.addEventListener('click', () => {
      this.togglePushToTalk();
    });

    // Spacebar shortcut
    window.addEventListener('keydown', (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        this.togglePushToTalk();
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        this.replayLastAudio();
      }
    });

    // Voice Suggestion Chips
    document.querySelectorAll('.chip-prompt').forEach(chip => {
      chip.addEventListener('click', () => {
        const prompt = chip.getAttribute('data-prompt');
        this.sendTextInteraction(prompt);
      });
    });

    // Manual text input
    if (this.sendTextBtn) {
      this.sendTextBtn.addEventListener('click', () => {
        const text = this.customPromptInput.value.trim();
        if (text) this.sendTextInteraction(text);
      });
    }

    if (this.customPromptInput) {
      this.customPromptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const text = this.customPromptInput.value.trim();
          if (text) this.sendTextInteraction(text);
        }
      });
    }

    // Replay Button
    this.replayBtn.addEventListener('click', () => this.replayLastAudio());

    // Settings Modal Open/Close
    document.getElementById('settings-open-btn').addEventListener('click', () => {
      this.settingsModal.classList.add('open');
    });
    document.getElementById('settings-close-btn').addEventListener('click', () => {
      this.settingsModal.classList.remove('open');
    });
    document.getElementById('save-settings-btn').addEventListener('click', () => {
      this.saveSettings();
    });

    // Camera selector change
    this.cameraSelect.addEventListener('change', (e) => {
      this.initCamera(e.target.value);
    });

    // Cancel / Stop button + Escape key
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener('click', () => this.cancelInteraction());
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.cancelInteraction();
    });

    // Fast mode toggle — update label text
    if (this.fastModeCheckbox) {
      this.fastModeCheckbox.addEventListener('change', () => {
        const on = this.fastModeCheckbox.checked;
        const label = document.querySelector('.speed-text');
        if (label) {
          label.textContent = on
            ? '⚡ Fast Mode: ON (Sub-Second Instant Speech)'
            : 'Fast Mode: OFF (Gemini Neural Voice)';
        }
      });
    }
  }

  cancelInteraction() {
    if (this.currentAbortController) {
      this.currentAbortController.abort();
      this.currentAbortController = null;
    }
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
    if (this.audioPlayer) {
      this.audioPlayer.pause();
      this.audioPlayer.src = '';
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    this.setProcessingState(false);
    this.mainActionBtn.classList.remove('recording');
    this.actionIcon.textContent = '🎙️';
    this.actionText.textContent = 'Hold or Tap to Talk to Glasses (Spacebar)';
    this.audioStatusLabel.textContent = 'AUDIO: IDLE';
    if (this.cancelBtn) this.cancelBtn.style.display = 'none';
    this.hudTranscript.textContent = 'Cancelled.';
  }

  captureFrameBase64() {
    const ctx = this.canvas.getContext('2d');
    if (this.video && this.video.videoWidth > 0) {
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
      return this.canvas.toDataURL('image/jpeg', 0.85);
    } else {
      return this.canvas.toDataURL('image/jpeg', 0.85);
    }
  }

  triggerShutter(imageB64) {
    // Camera flash animation
    if (this.shutterFlash) {
      this.shutterFlash.classList.remove('flashing');
      void this.shutterFlash.offsetWidth; // force browser reflow to re-trigger
      this.shutterFlash.classList.add('flashing');
      setTimeout(() => {
        this.shutterFlash.classList.remove('flashing');
      }, 150);
    }

    // Display captured snapshot thumbnail picture-in-picture
    if (this.snapshotPip && this.snapshotPipImg && imageB64) {
      this.snapshotPip.style.display = 'block';
      this.snapshotPipImg.src = imageB64;
    }
  }

  // PUSH-TO-TALK (Unified Mode-Free Trigger)
  async togglePushToTalk() {
    if (this.isProcessing) return;

    if (this.isRecording) {
      this.stopPushToTalk();
    } else {
      await this.startPushToTalk();
    }
  }

  async startPushToTalk() {
    try {
      // 1. If captureTiming is 'start' (default), take snapshot IMMEDIATELY
      // Wearer can put their phone/object down right away!
      if (this.captureTiming === 'start') {
        this.currentCapturedImage = this.captureFrameBase64();
        this.triggerShutter(this.currentCapturedImage);
      }

      // 2. Start audio stream
      if (!this.mediaStream) {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      this.audioChunks = [];
      const options = MediaRecorder.isTypeSupported('audio/webm') ? { mimeType: 'audio/webm' } : {};
      this.mediaRecorder = new MediaRecorder(this.mediaStream, options);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) this.audioChunks.push(e.data);
      };

      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType || 'audio/webm' });
        await this.processMultimodalInteraction(this.currentCapturedImage, audioBlob, null);
      };

      this.mediaRecorder.start();
      this.isRecording = true;

      // Update UI
      this.mainActionBtn.classList.add('recording');
      this.actionIcon.textContent = '🔴';
      this.actionText.textContent = 'Listening... Tap or Spacebar to Send';
      this.audioStatusLabel.textContent = 'AUDIO: LISTENING';
      this.hudTranscript.textContent = '📸 Frame captured! Tell Gemini: "Translate this", "What\'s in front of me?", etc.';
      this.hudStatusBadge.textContent = 'LISTENING TO WEARER';

    } catch (err) {
      console.error('Failed to start microphone recording');
      alert('Microphone access is needed. Please grant microphone permissions.');
    }
  }

  stopPushToTalk() {
    if (this.mediaRecorder && this.isRecording) {
      // If captureTiming is 'end', take snapshot when releasing button
      if (this.captureTiming === 'end') {
        this.currentCapturedImage = this.captureFrameBase64();
        this.triggerShutter(this.currentCapturedImage);
      }

      this.mediaRecorder.stop();
      this.isRecording = false;
      this.mainActionBtn.classList.remove('recording');
      this.actionIcon.textContent = '🎙️';
      this.actionText.textContent = 'Hold or Tap to Talk to Glasses (Spacebar)';
      this.audioStatusLabel.textContent = 'AUDIO: PROCESSING';
      this.hudStatusBadge.textContent = 'ANALYZING MULTIMODAL CORTEX';
    }
  }

  async sendTextInteraction(text) {
    if (this.isProcessing) return;
    const imageB64 = this.captureFrameBase64();
    this.triggerShutter(imageB64);
    await this.processMultimodalInteraction(imageB64, null, text);
  }

  async processMultimodalInteraction(imageB64, audioBlob = null, textPrompt = null) {
    this.setProcessingState(true, 'GEMINI THINKING & ANALYZING...');
    const startTime = performance.now();

    // Set up abort controller and show Stop button
    this.currentAbortController = new AbortController();
    if (this.cancelBtn) this.cancelBtn.style.display = 'flex';

    try {
      let audioBase64 = null;
      let audioMime = 'audio/webm';

      if (audioBlob) {
        audioMime = audioBlob.type || 'audio/webm';
        const reader = new FileReader();
        const base64Promise = new Promise((resolve) => {
          reader.onloadend = () => resolve(reader.result);
        });
        reader.readAsDataURL(audioBlob);
        audioBase64 = await base64Promise;
      }

      const voice = this.getVoice();
      const apiKey = this.getApiKey();
      const fastMode = this.fastModeCheckbox ? this.fastModeCheckbox.checked : true;

      const headers = { 'Content-Type': 'application/json' };
      if (apiKey) headers['x-gemini-api-key'] = apiKey;

      const res = await fetch('/api/interact', {
        method: 'POST',
        headers,
        signal: this.currentAbortController.signal,
        body: JSON.stringify({
          image_base64: imageB64,
          image_mime_type: 'image/jpeg',
          audio_base64: audioBase64,
          audio_mime_type: audioMime,
          text_prompt: textPrompt,
          voice: voice,
          generate_tts: !fastMode
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Multimodal interaction failed');
      }

      const data = await res.json();
      this.displayResults(data);
      this.handleAudioOutput(data.spoken_response, data.audio_url);

    } catch (err) {
      if (err.name === 'AbortError') {
        // User cancelled — already handled by cancelInteraction()
        return;
      }
      console.error('Interaction error:', err);
      this.hudTranscript.textContent = `Error: ${err.message}`;
    } finally {
      this.currentAbortController = null;
      if (this.cancelBtn) this.cancelBtn.style.display = 'none';
      this.setProcessingState(false);
    }
  }

  displayResults(data) {
    // HUD Marquee
    this.hudTranscript.textContent = data.spoken_response;
    this.spokenDisplay.textContent = data.spoken_response;

    // Dialogue Boxes
    this.wearerQueryDisplay.textContent = `"${data.user_query}"`;
    this.aiResponseDisplay.textContent = data.spoken_response;

    // Intent Badge
    const formattedIntent = (data.intent || 'Perception').replace('_', ' ').toUpperCase();
    this.detectedIntentBadge.textContent = formattedIntent;

    // Visual Tags & Obstacles
    this.visualTagsContainer.innerHTML = '';
    if (data.detected_tags && data.detected_tags.length > 0) {
      data.detected_tags.forEach(tag => {
        const chip = document.createElement('div');
        chip.className = 'object-chip';
        chip.innerHTML = `<span>📍 ${tag}</span>`;
        this.visualTagsContainer.appendChild(chip);
      });
    } else {
      this.visualTagsContainer.innerHTML = '<span style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">No specific tags detected</span>';
    }

    // Extra Details / Cultural Tips
    if (data.details && data.details.trim()) {
      this.extraDetailsContainer.style.display = 'block';
      this.extraDetailsText.textContent = data.details;
    } else {
      this.extraDetailsContainer.style.display = 'none';
    }
  }

  // AUDIO OUTPUT & PLAYBACK
  handleAudioOutput(spokenText, audioUrl) {
    this.lastSpokenText = spokenText;
    this.lastAudioUrl = audioUrl;
    this.replayBtn.disabled = false;

    if (audioUrl) {
      this.audioPlayer.src = audioUrl;
      this.audioPlayer.play().catch(e => console.warn('Audio autoplay prevented:', e));
      this.ttsBadge.textContent = `Gemini Neural Voice (${this.getVoice()})`;
      this.audioStatusLabel.textContent = 'AUDIO: SPEAKING (GEMINI)';
      this.audioPlayer.onended = () => {
        this.audioStatusLabel.textContent = 'AUDIO: IDLE';
      };
    } else {
      this.speakBrowserTTS(spokenText);
      this.ttsBadge.textContent = 'Browser Speech Synthesizer (Fallback)';
    }
  }

  speakBrowserTTS(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    this.audioStatusLabel.textContent = 'AUDIO: SPEAKING (BROWSER)';
    utterance.onend = () => {
      this.audioStatusLabel.textContent = 'AUDIO: IDLE';
    };
    window.speechSynthesis.speak(utterance);
  }

  replayLastAudio() {
    if (this.lastAudioUrl) {
      this.audioPlayer.currentTime = 0;
      this.audioPlayer.play();
      this.audioStatusLabel.textContent = 'AUDIO: REPLAYING';
      this.audioPlayer.onended = () => {
        this.audioStatusLabel.textContent = 'AUDIO: IDLE';
      };
    } else if (this.lastSpokenText) {
      this.speakBrowserTTS(this.lastSpokenText);
    }
  }

  async fetchAssetAsBase64(url) {
    const res = await fetch(url);
    const blob = await res.blob();
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  }

  async fetchAssetAsBlob(url) {
    const res = await fetch(url);
    return await res.blob();
  }

  setProcessingState(isProcessing, statusMessage = '') {
    this.isProcessing = isProcessing;
    this.mainActionBtn.disabled = isProcessing;
    if (isProcessing) {
      this.hudVisionStatus.textContent = statusMessage;
      this.hudTranscript.textContent = statusMessage;
      this.connectionDot.classList.add('busy');
    } else {
      this.connectionDot.classList.remove('busy');
    }
  }
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.scribeApp = new SmartGlassesApp();
});

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import config
from services import gemini_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_glasses")

app = FastAPI(
    title="Gemini Smart Glasses I/O Module",
    description="Multimodal event-driven AI assistant for smart glasses using Gemini 3.8 Flash and Gemini 3.1 Flash TTS",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class SeeRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded JPEG/PNG frame")
    mime_type: str = Field("image/jpeg", description="MIME type of image")
    prompt: Optional[str] = Field(None, description="Optional custom user query")
    voice: Optional[str] = Field(None, description="Preferred TTS voice")

class TranslateVisualRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image with foreign text")
    mime_type: str = Field("image/jpeg", description="MIME type of image")
    target_lang: str = Field("English", description="Target translation language")
    voice: Optional[str] = Field(None, description="Preferred TTS voice")

class ConverseRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio snippet")
    mime_type: str = Field("audio/webm", description="MIME type of audio")
    target_lang: str = Field("English", description="Target language to translate into")
    user_role: str = Field("foreign_speaker", description="'foreign_speaker' or 'wearer'")
    voice: Optional[str] = Field(None, description="Preferred TTS voice")

class InteractRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64 encoded JPEG/PNG frame")
    image_mime_type: str = Field("image/jpeg", description="MIME type of image")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio clip")
    audio_mime_type: str = Field("audio/webm", description="MIME type of audio")
    text_prompt: Optional[str] = Field(None, description="Optional text command or question")
    voice: Optional[str] = Field(None, description="Preferred TTS voice")
    generate_tts: bool = Field(False, description="Generate server neural TTS (slower) or client fast speech")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Preferred TTS voice")

# Endpoints
@app.get("/api/health")
def health_check():
    """Returns system status and configuration."""
    has_env_key = bool(config.GEMINI_API_KEY)
    return {
        "status": "online",
        "has_api_key": has_env_key,
        "vision_model": config.VISION_MODEL,
        "tts_model": config.TTS_MODEL,
        "default_voice": config.DEFAULT_TTS_VOICE,
        "supported_voices": ["Kore", "Puck", "Fenrir", "Aoede"]
    }

@app.post("/api/interact")
async def api_interact(
    req: InteractRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Unified Smart Glasses Interaction endpoint:
    Wearer presses button and speaks (e.g. 'Translate this', 'What is in front of me?').
    Simultaneously processes camera snapshot and audio command.
    """
    try:
        result = gemini_service.process_smart_glasses_interaction(
            image_b64=req.image_base64,
            image_mime_type=req.image_mime_type,
            audio_b64=req.audio_base64,
            audio_mime_type=req.audio_mime_type,
            text_prompt=req.text_prompt,
            voice=req.voice,
            generate_tts=req.generate_tts,
            api_key=x_gemini_api_key
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in /api/interact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/see")
async def api_see(
    req: SeeRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Mode 1 — See: Visual Assistant for Blind / Low-Vision navigation."""
    try:
        result = gemini_service.analyze_scene(
            image_b64=req.image_base64,
            mime_type=req.mime_type,
            user_prompt=req.prompt,
            voice=req.voice,
            api_key=x_gemini_api_key
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in /api/see: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate-visual")
async def api_translate_visual(
    req: TranslateVisualRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Mode 2 — Translate: Vision OCR and translation for signs/menus."""
    try:
        result = gemini_service.translate_sign(
            image_b64=req.image_base64,
            mime_type=req.mime_type,
            target_lang=req.target_lang,
            voice=req.voice,
            api_key=x_gemini_api_key
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in /api/translate-visual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/converse")
async def api_converse(
    req: ConverseRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Mode 3 — Converse: Speech-to-speech conversational translation."""
    try:
        result = gemini_service.translate_speech(
            audio_b64=req.audio_base64,
            mime_type=req.mime_type,
            target_lang=req.target_lang,
            user_role=req.user_role,
            voice=req.voice,
            api_key=x_gemini_api_key
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in /api/converse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def api_tts(
    req: TTSRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Dedicated TTS generation endpoint."""
    try:
        audio_url = gemini_service.synthesize_speech(
            text=req.text,
            voice=req.voice,
            api_key=x_gemini_api_key
        )
        return {
            "text": req.text,
            "audio_url": audio_url,
            "tts_available": audio_url is not None
        }
    except Exception as e:
        logger.error(f"Error in /api/tts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/presets")
def get_presets():
    """Return preloaded demo scenarios for instant hackathon demonstrations."""
    presets = [
        {
            "id": "translate_sign",
            "title": "Translate Sign",
            "prompt": "Translate this for me",
            "description": "Japanese sign: 地下鉄 銀座線 改札口 (Subway Ginza Line)",
            "file": "/static/presets/japanese_sign.jpg",
            "type": "image"
        },
        {
            "id": "room_nav",
            "title": "What's in front of me?",
            "prompt": "Tell me what's in front of me and if there are any obstacles",
            "description": "Room with coffee table, low chair, cables, and hallway exit.",
            "file": "/static/presets/room_obstacles.jpg",
            "type": "image"
        },
        {
            "id": "paris_menu",
            "title": "Read French Menu",
            "prompt": "What does this menu say and what is today's special?",
            "description": "French bistro menu with Plat du Jour & Euro prices.",
            "file": "/static/presets/french_menu.jpg",
            "type": "image"
        },
        {
            "id": "mandarin_direction",
            "title": "Translate Spoken Speech",
            "prompt": "Translate what this person is asking in English",
            "description": "Foreign traveler asking for directions in Mandarin.",
            "file": "/static/presets/mandarin_speech.wav",
            "type": "audio"
        }
    ]
    return {"presets": presets}

# Mount static folder
os.makedirs(config.STATIC_DIR, exist_ok=True)
os.makedirs(config.PRESETS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = config.STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        {"message": "Gemini Smart Glasses API is running. static/index.html is being prepared."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)


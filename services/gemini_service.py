import base64
import io
import json
import re
import wave
import logging
from typing import Optional, Dict, Any, List

from google import genai
import config

logger = logging.getLogger(__name__)

def get_client(api_key: Optional[str] = None) -> genai.Client:
    """Initialize and return a GenAI client with given or configured API key."""
    key = (api_key or config.GEMINI_API_KEY).strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Please provide an API key in .env or via settings.")
    return genai.Client(api_key=key)

def pcm_to_wav_bytes(pcm_bytes: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
    """Convert raw PCM audio bytes to WAV container bytes for standard browser playback."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def extract_json_or_text(text: str) -> Dict[str, Any]:
    """Extract structured JSON from model output or provide fallback structure."""
    if not text:
        return {}
    
    # Try finding markdown JSON block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    # Try searching for outermost curly braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace+1])
        except Exception:
            pass

    return {"raw_text": text}

def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[str]:
    """
    Generate speech using Gemini TTS (gemini-3.1-flash-tts-preview).
    Returns a data URI string 'data:audio/wav;base64,...' or None on failure.
    """
    if not text or not text.strip():
        return None

    voice_name = voice or config.DEFAULT_TTS_VOICE
    try:
        client = get_client(api_key)
        tts_interaction = client.interactions.create(
            model=config.TTS_MODEL,
            input=f"Say clearly and naturally: {text.strip()}",
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [
                    {"voice": voice_name}
                ]
            }
        )

        if tts_interaction and getattr(tts_interaction, "output_audio", None) and tts_interaction.output_audio.data:
            pcm_data = base64.b64decode(tts_interaction.output_audio.data)
            wav_bytes = pcm_to_wav_bytes(pcm_data)
            wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            return f"data:audio/wav;base64,{wav_b64}"
    except Exception as e:
        logger.warning(f"Gemini TTS generation notice: {e}. Client will fallback to Web Speech API.")
        return None

def analyze_scene(
    image_b64: str,
    mime_type: str = "image/jpeg",
    user_prompt: Optional[str] = None,
    voice: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mode 1 — See: Visual Assistant for Blind / Low-Vision Users.
    Analyzes room/environment, hazards, spatial layout, and objects.
    """
    client = get_client(api_key)
    custom_query = f"\nUser specific question: \"{user_prompt}\"" if user_prompt else ""

    system_instruction = (
        "You are an AI perception & mobility assistant integrated into Smart Glasses for a visually impaired user. "
        "Analyze this camera snapshot. Be concise, direct, calm, and accurate. "
        "Prioritize safety hazards (stairs, obstacles, curbs, glass doors, low overhangs) and immediate spatial orientation. "
        "Respond in strictly valid JSON format with these exact keys:\n"
        "{\n"
        '  "spoken_description": "A concise 1-2 sentence natural, direct audio description to be spoken into the user earpiece.",\n'
        '  "hazards": ["List of immediate navigation hazards or obstacles with relative positions, or empty list if none"],\n'
        '  "detected_objects": [{"label": "object name", "position": "left / center / right / 2 meters ahead"}],\n'
        '  "scene_type": "Brief classification e.g. indoor living room, sidewalk, office, kitchen",\n'
        '  "details": "Additional helpful spatial details for low-vision navigation"\n'
        "}"
        f"{custom_query}"
    )

    clean_b64 = image_b64.split(",")[-1] if "," in image_b64 else image_b64

    interaction = client.interactions.create(
        model=config.VISION_MODEL,
        input=[
            {"type": "text", "text": system_instruction},
            {"type": "image", "data": clean_b64, "mime_type": mime_type}
        ]
    )

    raw_output = interaction.output_text or ""
    parsed = extract_json_or_text(raw_output)

    spoken_text = parsed.get("spoken_description") or parsed.get("raw_text") or "No obstacles detected ahead."
    
    # Generate audio
    audio_data_uri = synthesize_speech(spoken_text, voice=voice, api_key=api_key)

    return {
        "mode": "see",
        "spoken_text": spoken_text,
        "hazards": parsed.get("hazards", []),
        "detected_objects": parsed.get("detected_objects", []),
        "scene_type": parsed.get("scene_type", "Unknown environment"),
        "details": parsed.get("details", ""),
        "raw_text": raw_output,
        "audio_url": audio_data_uri,
        "tts_available": audio_data_uri is not None
    }

def translate_sign(
    image_b64: str,
    mime_type: str = "image/jpeg",
    target_lang: str = "English",
    voice: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mode 2 — Translate: Vision OCR & Cultural Interpretation for Travelers.
    Reads signs, menus, or warning notices and translates them.
    """
    client = get_client(api_key)

    system_instruction = (
        f"You are a real-time vision translator in Smart Glasses for an international traveler. "
        f"Analyze the camera snapshot. Find any foreign text, signs, menus, labels, or notices. "
        f"Translate everything to {target_lang}. "
        "Respond in strictly valid JSON format with these exact keys:\n"
        "{\n"
        '  "source_language": "Detected language of the sign (e.g. Japanese, Mandarin, Spanish, French)",\n'
        '  "original_text": "Transcribed original text from the image",\n'
        '  "translated_text": "Clear translation in target language",\n'
        '  "spoken_description": "A natural 1-sentence spoken explanation for the traveler earpiece (e.g. The sign says Exit to Ginza Subway Line, 50 meters ahead)",\n'
        '  "traveler_tip": "Brief helpful cultural context, warnings, or pricing note if applicable"\n'
        "}"
    )

    clean_b64 = image_b64.split(",")[-1] if "," in image_b64 else image_b64

    interaction = client.interactions.create(
        model=config.VISION_MODEL,
        input=[
            {"type": "text", "text": system_instruction},
            {"type": "image", "data": clean_b64, "mime_type": mime_type}
        ]
    )

    raw_output = interaction.output_text or ""
    parsed = extract_json_or_text(raw_output)

    spoken_text = parsed.get("spoken_description") or parsed.get("translated_text") or parsed.get("raw_text") or "No readable text found."
    audio_data_uri = synthesize_speech(spoken_text, voice=voice, api_key=api_key)

    return {
        "mode": "translate",
        "source_language": parsed.get("source_language", "Unknown"),
        "original_text": parsed.get("original_text", ""),
        "translated_text": parsed.get("translated_text", spoken_text),
        "spoken_text": spoken_text,
        "traveler_tip": parsed.get("traveler_tip", ""),
        "raw_text": raw_output,
        "audio_url": audio_data_uri,
        "tts_available": audio_data_uri is not None
    }

def translate_speech(
    audio_b64: str,
    mime_type: str = "audio/webm",
    target_lang: str = "English",
    user_role: str = "foreign_speaker", # 'foreign_speaker' (translate to English) or 'wearer' (translate to foreign)
    voice: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mode 3 — Converse: Push-to-Talk Speech-to-Speech Translation.
    Listens to speech, transcribes, translates, and synthesizes audio out.
    """
    client = get_client(api_key)

    system_instruction = (
        f"You are a real-time conversational interpreter in Smart Glasses. "
        f"The user has recorded a spoken audio clip. "
        f"Listen carefully to the audio. Transcribe the spoken words verbatim. "
        f"Identify the spoken language. Translate the message into {target_lang}. "
        "Respond in strictly valid JSON format with these exact keys:\n"
        "{\n"
        '  "source_language": "Detected language (e.g. Mandarin, Spanish, English)",\n'
        '  "transcription": "Verbatim transcription in the original spoken language",\n'
        '  "translated_text": "Translation in the target language",\n'
        '  "spoken_description": "The exact translated sentence to speak aloud to the listener",\n'
        '  "conversation_tone": "Brief tone note e.g. polite inquiry, asking for directions, greeting"\n'
        "}"
    )

    clean_b64 = audio_b64.split(",")[-1] if "," in audio_b64 else audio_b64

    interaction = client.interactions.create(
        model=config.CONVERSE_MODEL,
        input=[
            {"type": "text", "text": system_instruction},
            {"type": "audio", "data": clean_b64, "mime_type": mime_type}
        ]
    )

def process_smart_glasses_interaction(
    image_b64: Optional[str] = None,
    image_mime_type: str = "image/jpeg",
    audio_b64: Optional[str] = None,
    audio_mime_type: str = "audio/webm",
    text_prompt: Optional[str] = None,
    voice: Optional[str] = None,
    generate_tts: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified Smart Glasses Interaction:
    Takes visual snapshot + user's voice command/speech simultaneously.
    Gemini 3.8 Flash interprets what the user wants:
      - "Translate this for me" -> reads & translates visual text / signs
      - "Tell me what's in front of me" -> room & obstacle perception for blind assistance
      - "Translate what they are saying" -> speech-to-speech translation
      - General visual Q&A ("Where are my keys?", "What color is this?")
    """
    client = get_client(api_key)

    system_instruction = (
        "You are the multimodal AI cortex of an intelligent Smart Glasses wearable device. "
        "You are the fast multimodal AI cortex of an intelligent Smart Glasses wearable device. "
        "The wearer has pressed a button and is speaking to you while the glasses camera captures their view. "
        "You may receive a camera snapshot, an audio recording of their voice command or ambient speech, and/or text. "
        "Listen to the audio to understand what the wearer wants or what speech is occurring. "
        "Look at the image to see what the wearer is looking at. "
        "Dynamically execute their request: "
        "1. If they ask 'Tell me what is in front of me', 'What am I seeing?', or ask about their surroundings, "
        "   describe the visual environment concisely, prioritizing safety obstacles, steps, hazards, and key objects for audio delivery. "
        "2. If they ask 'Translate this for me', 'What does this sign say?', or ask to read text, "
        "   read the foreign text in the image, detect the language, translate it to English, and explain it clearly. "
        "3. If they ask to translate foreign speech, or the audio contains someone speaking a foreign language, "
        "   transcribe and translate the spoken conversation. "
        "4. If they ask any specific visual question ('Where is the door?', 'Is this milk expired?'), answer directly. "
        "Listen to the audio to understand what the wearer wants. Look at the camera snapshot. "
        "Dynamically execute their request with high speed and conciseness: "
        "1. If they ask 'Tell me what is in front of me' or about surroundings: describe the visual environment concisely, prioritizing safety obstacles, hazards, and key objects. "
        "2. If they ask 'Translate this' or to read signs/menus: read foreign text in the image, detect the language, and translate it to English clearly. "
        "3. If they ask to translate foreign speech: transcribe and translate the conversation into English. "
        "4. If they ask a specific visual question: answer directly. "
        "\n"
        "Respond in strictly valid JSON format with these exact keys:\n"
        "Keep your response strictly under 2 sentences, direct, clear, and conversational. "
        "Respond in valid JSON format with these exact keys:\n"
        "{\n"
        '  "user_query": "Transcribed text of what the user asked in the audio clip (or text prompt)",\n'
        '  "intent": "Brief intent label e.g. scene_perception, sign_translation, speech_translation, visual_qa",\n'
        '  "spoken_response": "Concise, natural 1-2 sentence answer to be spoken directly into the user earpiece / speaker.",\n'
        '  "detected_tags": ["List of detected objects, obstacles, or translated phrases"],\n'
        '  "details": "Additional helpful structured notes, original text, or navigation tips if relevant"\n'
        '  "user_query": "Short transcription of what the user asked",\n'
        '  "intent": "Short intent label e.g. scene_perception, sign_translation, speech_translation, visual_qa",\n'
        '  "spoken_response": "Concise 1-2 sentence answer to be spoken immediately into the user earpiece.",\n'
        '  "detected_tags": ["List of detected objects, hazards, or translated phrases"],\n'
        '  "details": "Optional brief note or translation details"\n'
        "}"
    )

    contents: List[Dict[str, Any]] = [
        {"type": "text", "text": system_instruction}
    ]

    # Add visual context if provided
    if image_b64 and image_b64.strip():
        clean_img_b64 = image_b64.split(",")[-1] if "," in image_b64 else image_b64
        contents.append({
            "type": "image",
            "data": clean_img_b64,
            "mime_type": image_mime_type
        })

    # Add audio voice command if provided
    if audio_b64 and audio_b64.strip():
        clean_aud_b64 = audio_b64.split(",")[-1] if "," in audio_b64 else audio_b64
        contents.append({
            "type": "audio",
            "data": clean_aud_b64,
            "mime_type": audio_mime_type
        })

    # Add text prompt if provided as secondary/fallback input
    if text_prompt and text_prompt.strip():
        contents.append({
            "type": "text",
            "text": f"Wearer command: {text_prompt.strip()}"
        })

    interaction = client.interactions.create(
        model=config.VISION_MODEL,
        input=contents
    )

    raw_output = interaction.output_text or ""
    parsed = extract_json_or_text(raw_output)

    spoken_text = parsed.get("spoken_response") or parsed.get("raw_text") or "I processed your request."
    user_query = parsed.get("user_query") or text_prompt or "(Voice command processed)"
    intent = parsed.get("intent") or "multimodal_assistance"
    detected_tags = parsed.get("detected_tags") or []
    details = parsed.get("details") or ""

    # Synthesize speech
    audio_data_uri = synthesize_speech(spoken_text, voice=voice, api_key=api_key)
    # Synthesize speech only if requested (skipping this cuts latency by ~50-70%!)
    audio_data_uri = None
    if generate_tts:
        audio_data_uri = synthesize_speech(spoken_text, voice=voice, api_key=api_key)

    return {
        "user_query": user_query,
        "intent": intent,
        "spoken_response": spoken_text,
        "detected_tags": detected_tags,
        "details": details,
        "raw_text": raw_output,
        "audio_url": audio_data_uri,
        "tts_available": audio_data_uri is not None
    }



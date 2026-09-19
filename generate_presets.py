import os
import math
import struct
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

presets_dir = Path("/Users/viotune/Desktop/scribe/static/presets")
presets_dir.mkdir(parents=True, exist_ok=True)

def create_room_image():
    """Create a simulated room scene image for Mode 1 (See)."""
    img = Image.new("RGB", (960, 640), color=(240, 243, 246))
    draw = ImageDraw.Draw(img)

    # Floor and Walls
    draw.rectangle([0, 360, 960, 640], fill=(210, 180, 140)) # Wooden floor
    draw.rectangle([0, 0, 960, 360], fill=(230, 235, 240)) # Wall

    # Floor perspective lines
    for x in range(-200, 1200, 100):
        draw.line([(480, 360), (x, 640)], fill=(195, 165, 125), width=2)

    # Doorway in center
    draw.rectangle([400, 120, 560, 360], fill=(60, 60, 70))
    draw.rectangle([415, 135, 545, 360], fill=(255, 255, 255)) # Hallway bright light
    draw.text((430, 220), "EXIT / HALLWAY", fill=(80, 80, 80))

    # Low Coffee Table (Obstacle in path!)
    draw.rectangle([320, 440, 640, 520], fill=(120, 70, 30))
    draw.text((380, 470), "Low Coffee Table (Obstacle)", fill=(255, 255, 255))
    draw.rectangle([340, 520, 360, 580], fill=(90, 50, 20)) # Leg
    draw.rectangle([600, 520, 620, 580], fill=(90, 50, 20)) # Leg

    # Chair on the left
    draw.rectangle([100, 320, 240, 520], fill=(52, 110, 180))
    draw.rectangle([100, 420, 240, 450], fill=(40, 90, 150))
    draw.text((120, 380), "Office Chair", fill=(255, 255, 255))

    # Plant on the right
    draw.ellipse([760, 240, 880, 400], fill=(34, 139, 34))
    draw.rectangle([790, 380, 850, 480], fill=(178, 80, 30))
    draw.text((780, 420), "Potted Plant", fill=(255, 255, 255))

    # Loose cables warning
    draw.arc([260, 540, 440, 600], 0, 180, fill=(20, 20, 20), width=4)
    draw.text((250, 605), "Warning: Cable on floor", fill=(180, 20, 20))

    img.save(presets_dir / "room_obstacles.jpg", quality=92)
    print("Created room_obstacles.jpg")

def create_japanese_sign():
    """Create a realistic Japanese subway direction sign for Mode 2 (Translate)."""
    img = Image.new("RGB", (960, 540), color=(25, 30, 40))
    draw = ImageDraw.Draw(img)

    # Sign banner container
    draw.rectangle([60, 60, 900, 480], fill=(255, 255, 255), outline=(220, 220, 220), width=6)
    
    # Orange Ginza line header banner
    draw.rectangle([60, 60, 900, 160], fill=(243, 151, 0)) # Tokyo Metro Ginza Line Orange
    draw.text((100, 95), "Tokyo Metro / 東京メトロ", fill=(255, 255, 255))

    # Main Japanese Text and English Subtitle
    # Large simulated text blocks and clear romanization
    draw.text((100, 190), "地下鉄 銀座線 改札口", fill=(20, 20, 20))
    draw.text((100, 250), "Subway Ginza Line Ticket Gates", fill=(80, 80, 80))
    
    # Platform info
    draw.rectangle([100, 320, 320, 380], fill=(240, 240, 240), outline=(200, 200, 200))
    draw.text((120, 340), "1番線: 渋谷方面 (Shibuya)", fill=(30, 30, 30))

    draw.rectangle([360, 320, 580, 380], fill=(240, 240, 240), outline=(200, 200, 200))
    draw.text((380, 340), "2番線: 浅草方面 (Asakusa)", fill=(30, 30, 30))

    # Arrow to the right
    draw.polygon([(780, 310), (840, 350), (780, 390)], fill=(243, 151, 0))
    draw.rectangle([720, 335, 780, 365], fill=(243, 151, 0))

    # Caution note at bottom
    draw.rectangle([60, 420, 900, 480], fill=(245, 245, 245))
    draw.text((100, 440), "注意: 足元にご注意ください (Caution: Mind your step)", fill=(180, 30, 30))

    img.save(presets_dir / "japanese_sign.jpg", quality=95)
    print("Created japanese_sign.jpg")

def create_french_menu():
    """Create a French Bistro blackboard menu for Mode 2 (Translate)."""
    img = Image.new("RGB", (960, 600), color=(30, 35, 33)) # Blackboard
    draw = ImageDraw.Draw(img)

    # Chalk border
    draw.rectangle([40, 40, 920, 560], outline=(200, 200, 190), width=3)
    draw.text((330, 70), "LE BISTROT PARISIEN", fill=(255, 255, 255))
    draw.text((380, 110), "~ Menu du Jour ~", fill=(220, 210, 180))

    draw.text((80, 170), "Entrées :", fill=(230, 230, 150))
    draw.text((120, 210), "- Soupe à l'oignon gratinée maison ........ 9 €", fill=(240, 240, 240))
    draw.text((120, 250), "- Salade de chèvre chaud au miel ......... 11 €", fill=(240, 240, 240))

    draw.text((80, 310), "Plats :", fill=(230, 230, 150))
    draw.text((120, 350), "- Bœuf Bourguignon traditionnel ......... 18 €", fill=(240, 240, 240))
    draw.text((120, 390), "- Filet de saumon, riz basmati ........... 17 €", fill=(240, 240, 240))

    draw.text((80, 450), "Dessert :", fill=(230, 230, 150))
    draw.text((120, 490), "- Tarte Tatin tiède à la crème fraîche ... 8 €", fill=(240, 240, 240))

    img.save(presets_dir / "french_menu.jpg", quality=95)
    print("Created french_menu.jpg")

def create_sample_wav():
    """Create a simple synthetic tone WAV file so converse endpoint has a sample test file."""
    wav_path = presets_dir / "mandarin_speech.wav"
    sample_rate = 16000
    duration = 2.0
    num_samples = int(sample_rate * duration)
    
    # Generate two gentle musical tones (440Hz and 880Hz) to represent acoustic voice input
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Mix 440 Hz + modulation
            val = int(12000 * math.sin(2 * math.pi * 440 * t) * math.exp(-t * 0.5))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    print("Created mandarin_speech.wav")

if __name__ == "__main__":
    create_room_image()
    create_japanese_sign()
    create_french_menu()
    create_sample_wav()


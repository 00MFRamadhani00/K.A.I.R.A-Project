import openai
import winsound
import sys
import pytchat
import time
import re
import pyaudio
import keyboard
import wave
import threading
import json
import random
import logging
from config import *
from utils.translate import detect_google, translate_google
from utils.TTS import silero_tts, voicevox_tts
from utils.subtitle import *
from utils.promptMaker import *

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

# use your API Key from https://platform.openai.com/api-keys
openai.api_key = api_key

conversation = []
history = {"history": conversation}

mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Fadhil"
blacklist = ["Nightbot", "streamelements"]

stop_event = threading.Event()

# Read identity from file
def read_identity(identity_path):
    with open(identity_path, "r", encoding="utf-8") as file:
        identity = file.read().strip()
    return identity

identity_text = read_identity("characterConfig/KAIRA/identity.txt")

def greet_user():
    greetings = ["Hai! Ada yang bisa aku bantu hari ini? 😊", 
                 "Halo! Bagaimana aku bisa membantu Anda hari ini? 😄",
                 "Selamat datang! Ada yang bisa kubantu? 😀"]
    greeting_text = random.choice(greetings)
    translated_greeting_en = translate_google(greeting_text, 'ID', 'EN')  # Translate to English
    translated_greeting_ja = translate_google(greeting_text, 'ID', 'JA')  # Translate to Japanese
    print(greeting_text)
    # silero_tts(translated_greeting_en, filename="greeting.wav")
    voicevox_tts(translated_greeting_ja, filename="greeting.wav")
    winsound.PlaySound("greeting.wav", winsound.SND_FILENAME)

def say_goodbye():
    goodbyes = ["Sampai jumpa! Semoga harimu menyenangkan! 👋",
                "Bye! Sampai ketemu lagi ya! 😊",
                "Sampai nanti! Jaga diri, ya! 😄"]
    goodbye_text = random.choice(goodbyes)
    translated_goodbye_en = translate_google(goodbye_text, 'ID', 'EN')  # Translate to English
    translated_goodbye_ja = translate_google(goodbye_text, 'ID', 'JA')  # Translate to Japanese
    print(goodbye_text)
    # silero_tts(translated_goodbye_en, filename="goodbye.wav")
    voicevox_tts(translated_goodbye_ja, filename="goodbye.wav")
    winsound.PlaySound("goodbye.wav", winsound.SND_FILENAME)

def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    except Exception as e:
        logging.error(f"Error opening audio stream: {e}")
        return

    frames = []
    print("Recording...")
    try:
        while keyboard.is_pressed('RIGHT_SHIFT'):
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        pass

    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio("input.wav")

def transcribe_audio(file):
    global chat_now
    try:
        with open(file, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            chat_now = transcript.text
            print("Question: " + chat_now)
            logging.info(f"Transcription: {chat_now}")
    except Exception as e:
        logging.error(f"Error transcribing audio: {e}")
        return

    result = owner_name + " said " + chat_now
    conversation.append({'role': 'user', 'content': result})
    openai_answer()

def openai_answer():
    global total_characters, conversation

    total_characters = sum(len(d['content']) for d in conversation)

    while total_characters > 4000:
        try:
            conversation.pop(2)
            total_characters = sum(len(d['content']) for d in conversation)
        except Exception as e:
            logging.error(f"Error removing old messages: {e}")

    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    prompt = getPrompt()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=prompt,
            max_tokens=2000,
            temperature=1,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        message = response['choices'][0]['message']['content']
        
        conversation.append({'role': 'assistant', 'content': message})
        translate_text(message)
    except Exception as e:
        logging.error(f"Error getting answer from OpenAI: {e}")

def yt_livechat(video_id):
    global chat
    live = pytchat.create(video_id=video_id)
    while live.is_alive() and not stop_event.is_set():
        try:
            for c in live.get().sync_items():
                if c.author.name in blacklist:
                    continue
                
                if not c.message.startswith("!"):
                    chat_raw = re.sub(r':[^\s]+:', '', c.message)
                    chat_raw = chat_raw.replace('#', '')
                    chat = c.author.name + ' : ' + chat_raw
                    print(chat)
                    logging.info(f"Received chat: {chat}")
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error receiving chat: {e}")

def translate_text(text):
    global is_Speaking
    
    try:
        detect = detect_google(text)
        tts = translate_google(text, detect, "JA")
        tts_en = translate_google(text, detect, "EN")
        tts_id = translate_google(text, detect, "ID")
        print(f"Jawaban: {tts_id}")
    except Exception as e:
        logging.error(f"Error in translation: {e}")
        return

    voicevox_tts(tts)
    generate_subtitle(chat_now, text)

    time.sleep(1)

    is_Speaking = True
    winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    is_Speaking = False

    time.sleep(1)
    with open("output.txt", "w") as f:
        f.truncate(0)
    with open("chat.txt", "w") as f:
        f.truncate(0)

def preparation():
    global conversation, chat_now, chat, chat_prev
    conversation.append(getIdentity("characterConfig/KAIRA/identity.txt"))  # Add identity to the initial conversation
    while True:
        chat_now = chat
        if not is_Speaking and chat_now != chat_prev:
            conversation.append({'role': 'user', 'content': chat_now})
            chat_prev = chat_now
            conversation.append({'role': 'system', 'content': 'Berikan jawaban yang lebih panjang dan detail.'})
            openai_answer()
        if stop_event.is_set():
            break
        time.sleep(1)

def run():
    global mode
    try:
        greet_user()
        
        mode = input("Mode (1-Mic, 2-Youtube Live): ")

        if mode == "1":
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed('RIGHT_SHIFT'):
                    record_audio()
            
        elif mode == "2":
            live_id = input("Livestream ID: ")
            t = threading.Thread(target=preparation)
            t.start()
            yt_livechat(live_id)
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
        stop_event.set()   # Stop the background thread
        say_goodbye()
        if 't' in locals():
            t.join()
        print("Stopped")

if __name__ == "__main__":
    run()
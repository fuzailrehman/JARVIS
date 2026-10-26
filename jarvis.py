import os
import re
import time
import subprocess
import asyncio
import pygame
import speech_recognition as sr
from google import genai
import keyboard
import pyautogui
import glob
from pathlib import Path
import pyttsx3
jarvis_active = True
import difflib
import webbrowser
import winreg
import urllib.parse
import pygame
import edge_tts

pygame.mixer.init()

# AndrewNeural voice Brian se zyada solid aur heavy hoti hai
VOICE = "en-US-AndrewNeural"

async def _generate_audio(text, output_file):
    # Pitch ko -15Hz kar diya hai taake aawaz ekdum bhari aur cinematic ho jaye
    # rate='+10%' se speed tez rahegi taake mureel ya slow feel na ho
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%", pitch="-15Hz")
    await communicate.save(output_file)

def speak(text):
    clean_text = re.sub(r'\*+', '', text)
    print(f"JARVIS: {clean_text}")
    
    file_path = "voice_temp.mp3"
    
    try:
        # Audio file generate karna
        asyncio.run(_generate_audio(clean_text, file_path))
        
        # Audio play karna
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)
            
        pygame.mixer.music.unload()
        
        # Temp file clean karna
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Speech error: {e}")

def play_on_youtube(query):
    clean_query = query.lower()
    for word in ["play", "search", "on", "youtube", "jarvis", "please", "song", "gaana", "chalao"]:
        clean_query = clean_query.replace(word, " ")
    
    target = clean_query.strip()
    
    if not target:
        speak("Kya search ya play karna hai, Boss?")
        return True

    speak(f"Playing {target} on YouTube, Boss.")
    encoded_target = urllib.parse.quote(target)
    yt_url = f"https://www.youtube.com/results?search_query={encoded_target}"

    try:
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.2)
        pyautogui.write(yt_url, interval=0.02)
        pyautogui.press('enter')
    except Exception:
        webbrowser.open(yt_url)
        
    return True
        
def toggle_jarvis():
    global jarvis_active
    jarvis_active = not jarvis_active
    if jarvis_active:
        speak("Systems online, Boss.")
    else:
        speak("Going to sleep, Boss.")

keyboard.add_hotkey('ctrl+alt+j', toggle_jarvis)

apui_keys = [
    
current_key_index = 0

def get_jarvis_engine():
    global current_key_index
    key = API_KEYS[current_key_index]
    return genai.Client(api_key=key)

jarvis_engine = get_jarvis_engine()


def search_and_open_file(query):
    # Faltu words saaf karna taake pure target name par focus ho
    clean_query = query.lower()
    for word in ["search", "find", "open", "file", "folder", "jarvis", "please", "a", "an", "the", "how", "is", "can", "you", "kholo", "chalao", "dhoondo", "meri"]:
        clean_query = clean_query.replace(word, " ")
    
    target = clean_query.strip()
    
    if not target:
        speak("Could you please specify the target name, Boss?")
        return True

    speak(f"Scanning local sectors for {target}, Sir.")

    # Speed Optimization: Sabse pehle primary fast locations scan hongi (Zero Latency)
    primary_paths = [
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.home() / "Documents"
    ]

    target_words = target.split()
    matched_folders = {}
    matched_files = {}

    # Step 1: Lightning-fast scan in primary user folders
    for base_path in primary_paths:
        if base_path.exists():
            try:
                for root, dirs, files in os.walk(base_path):
                    # Main Folders check (jaise GTA V, cs50p, etc.)
                    for d in dirs:
                        d_lower = d.lower()
                        if all(w in d_lower for w in target_words):
                            matched_folders[d_lower] = os.path.join(root, d)

                    # Files check (ignoring junk/system cache files to prevent false matches)
                    for f in files:
                        f_lower = f.lower()
                        if f_lower.endswith(('.log', '.cache', '.xml', '.ini', '.rgl', '.tmp', '.sys')):
                            continue
                        if all(w in f_lower for w in target_words):
                            matched_files[f_lower] = os.path.join(root, f)
            except PermissionError:
                continue

    # Priority 1: Main Folder mil gaya toh foran khol do
    if matched_folders:
        best_folder_name = min(matched_folders.keys(), key=len)
        best_folder_path = matched_folders[best_folder_name]
        speak("Main directory located. Accessing it now, Boss.")
        try:
            os.startfile(best_folder_path)
        except Exception:
            subprocess.run(f'explorer "{best_folder_path}"')
        return True

    # Priority 2: Main File mil gayi toh foran khol do
    if matched_files:
        best_file_name = min(matched_files.keys(), key=len)
        best_file_path = matched_files[best_file_name]
        speak("File found. Launching it right away, Sir.")
        try:
            os.startfile(best_file_path)
        except Exception:
            subprocess.run(f'explorer /select, "{best_file_path}"')
        return True

    # Step 2: Smart Secondary Check (Agar primary mein na ho, toh C aur D drives ke main folders check karega bina hang hue)
    secondary_paths = [Path("C:\\"), Path("D:\\")]
    for base_path in secondary_paths:
        if base_path.exists():
            try:
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        if all(w in item.lower() for w in target_words):
                            speak("System directory located. Opening now, Boss.")
                            os.startfile(item_path)
                            return True
            except Exception:
                continue

    # Step 3: Fuzzy Match Backup (Agar spelling thodi bohot aage peeche ho)
    all_combined = {}
    for base_path in primary_paths:
        if base_path.exists():
            try:
                for root, dirs, files in os.walk(base_path):
                    for d in dirs:
                        all_combined[d.lower()] = os.path.join(root, d)
            except PermissionError:
                continue

    if all_combined:
        close_matches = difflib.get_close_matches(target, list(all_combined.keys()), n=1, cutoff=0.35)
        if close_matches:
            suggested_name = close_matches[0]
            suggested_path = all_combined[suggested_name]
            speak("Similar match located. Opening it for you, Boss.")
            try:
                os.startfile(suggested_path)
            except Exception:
                subprocess.run(f'explorer "{suggested_path}"')
            return True

    # Final Boundary: Agar kahin na mile toh yahin stop karega, browser par kabhi nahi jayega
    speak("I'm afraid the requested file or folder is nowhere to be found on your system, Boss.")
    return True

def execute_system_command(query):
    # Original query ko محفوظ rakhna
    original_query = query
    query_lower = query.lower()
    
    # 1. File / Folder Search Check (Jaise "file GTA V" ya "dhoondo")
    if any(keyword in query_lower for keyword in ["file", "folder", "dhoondo", "search", "open file"]):
        clean_query = query_lower
        for word in ["search", "find", "open", "file", "folder", "jarvis", "please", "kholo", "chalao", "dhoondo", "meri"]:
            clean_query = clean_query.replace(word, " ")
        
        target = clean_query.strip()
        
        if not target:
            speak("Could you please specify the target name, Boss?")
            return True

        search_and_open_file(target)
        return True
    
# 2. Application Opening Check (Jaise "open Instagram" - bina "file" lafaz ke)
    if "open" in query_lower or "launch" in query_lower:
        clean_app = query_lower.replace("open", "").replace("launch", "").replace("jarvis", "").replace("please", "").strip()
        if clean_app:
            open_application(clean_app)
            return True
        
    # 3. Closing Apps / Windows Check
    elif "close" in query_lower or "band karo" in query_lower:
        if "chrome" in query:
            os.system("taskkill /f /im chrome.exe")
            speak("Closed Google Chrome, Boss.")
        elif "spotify" in query:
            os.system("taskkill /f /im spotify.exe")
            speak("Closed Spotify, Boss.")
        elif "code" in query or "vs code" in query:
            os.system("taskkill /f /im code.exe")
            speak("Closed VS Code, Boss.")
        elif "notepad" in query:
            os.system("taskkill /f /im notepad.exe")
            speak("Closed Notepad, Boss.")
        else:
            app_to_close = query.replace("close", "").replace("band karo", "").strip()
            if app_to_close:
                os.system(f"taskkill /f /im {app_to_close}.exe")
                speak(f"Closed {app_to_close}, Boss.")
            else:
                pyautogui.hotkey('alt', 'f4')
                speak("Closed active window, Boss.")
        return True

    # 4. YouTube Song & Music Play Check
    elif "play" in query or "song" in query or "gaana" in query or "youtube" in query:
        if "pause" in query or "resume" in query:
            pyautogui.press("playpause")
            speak("Media toggled, Boss.")
            return True
        play_on_youtube(query)
        return True

    # 5. Google Search Check
    elif "search" in query or "google" in query:
        search_query = query.lower().replace("search", "").replace("google", "").replace("jarvis", "").strip()
        if search_query:
            speak(f"Searching for {search_query} on Google, Boss.")
            encoded_google = urllib.parse.quote(search_query)
            webbrowser.open(f"https://www.google.com/search?q={encoded_google}")
        else:
            webbrowser.open("https://www.google.com")
            speak("Opening Google, Boss.")
        return True

    # 6. Volume & Media Controls
    elif "volume up" in query or "aawaz badao" in query or "volume badao" in query:
        pyautogui.press("volumeup", presses=5)
        speak("Volume increased, Boss.")
        return True
    elif "volume down" in query or "aawaz kam" in query or "volume kam" in query:
        pyautogui.press("volumedown", presses=5)
        speak("Volume decreased, Boss.")
        return True
    elif "mute" in query:
        pyautogui.press("volumemute")
        speak("Audio muted, Boss.")
        return True
    elif "pause" in query or "resume" in query or "stop media" in query:
        pyautogui.press("playpause")
        speak("Media toggled, Boss.")
        return True

    return False


recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

# انسانوں کی طرح صبر سے سننے کے لیے پرفیکٹ سیٹنگ
recognizer.pause_threshold = 1.8        # سوچنے کا ٹائم ملے گا، بیچ میں بات نہیں کاٹے گا
recognizer.non_speaking_duration = 0.8   # جب تو واقعی خاموش ہوگا تبھی ایگزیکیوٹ کرے گا

is_calibrated = False

def listen():
    global is_calibrated
    
    with sr.Microphone() as source:
        if not is_calibrated:
            print("\n[JARVIS] Calibrating audio environment, Boss...")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            is_calibrated = True
            print("[JARVIS] Audio systems online and ready.")

        print("\nListening, Boss...")
        try:
            # ۱۰ سیکنڈ کا ٹائم آؤٹ اور ۱۵ سیکنڈ کی لمبی فریز لمٹ
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("Recognizing...")
            ہماری اردگرد کی بولی اور ایکسینٹ بالکل صحیح پکڑتا ہے
            query = recognizer.recognize_google(audio, language='en-IN')
            print(f"You: {query}")
            return query.lower()
            
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception:
            return ""

def main():
    global jarvis_engine, current_key_index, jarvis_active
    
    system_prompt = (
        "You are JARVIS, an ultra-smart, loyal, and efficient AI butler and agent. "
        "Always address the user as 'Boss' or 'Sir'. Keep your answers extremely short, "
        "direct, and fast with a confident Iron Man movie vibe."
        "You are JARVIS. Respond strictly under 10 words unless writing code."
    )

    model_name = "gemini-3.6-flash"

    chat = jarvis_engine.chats.create(
        model=model_name,
        config={'system_instruction': system_prompt}
    )

    speak("All systems online, Boss. Awaiting your instructions.")

    while True:
        if not jarvis_active:
            time.sleep(0.5)
            continue

        query = listen()
        if not query:
            continue

        if any(word in query for word in ["exit", "bye", "shutdown", "quit"]):
            speak("Shutting down systems. Have a good time, Boss!")
            break

        if execute_system_command(query):
            continue

        start_time = time.time()
        success = False

        for attempt in range(len(API_KEYS)):
            try:
                response = chat.send_message(query)
                elapsed_time = round(time.time() - start_time, 2)
                print(f"[Response Time: {elapsed_time}s | Key {current_key_index + 1}]")
                speak(response.text)
                success = True
                break
            except Exception as e:
                current_key_index = (current_key_index + 1) % len(API_KEYS)
                print(f"Key Switch -> Moving to Key {current_key_index + 1}...")
                jarvis_engine = get_jarvis_engine()
                chat = jarvis_engine.chats.create(
                    model=model_name,
                    config={'system_instruction': system_prompt}
                )

def open_application(app_name):
    clean_app = app_name.lower().strip()
    speak(f"Opening {app_name}, Boss.")
    
    # 1. Pehle Windows ke Start Menu Shortcuts scan karenge (Fast & Clean)
    start_menu_paths = [
        Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs"
    ]
    
    target_query = clean_app.replace(" ", "")
    matched_shortcut = None
    
    for sp in start_menu_paths:
        if sp.exists():
            for p in sp.rglob("*.lnk"):
                if target_query in p.name.lower():
                    matched_shortcut = str(p)
                    break
            if matched_shortcut:
                break

    # Agar local shortcut mil gaya toh foran launch kar do
    if matched_shortcut:
        try:
            os.startfile(matched_shortcut)
            return
        except Exception:
            pass

    # 2. Windows Start Menu Search Automation (Real Keyboard Typing)
    # Yeh bilkul Start Menu khol kar search bar par type karega
    try:
        # Windows key press karega Start Menu kholne ke liye
        pyautogui.press('win')
        time.sleep(0.5)
        
        # Start bar mein app ka naam type karega
        pyautogui.write(clean_app, interval=0.05)
        time.sleep(0.8)
        
        # Enter press karega app launch karne ke liye
        pyautogui.press('enter')
        
    except Exception as e:
        speak(f"Boss, '{app_name}' Start Menu mein dhoondne mein masla hua hai.")

if __name__ == "__main__":
    main()

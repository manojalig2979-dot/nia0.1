import sys
import threading
from config_manager import load_config
from voice_engine import VoiceEngine
from agent_orchestrator import NiaAgentOrchestrator

def hands_free_voice_loop(agent: NiaAgentOrchestrator, voice: VoiceEngine, wake_word="nia"):
    """Continuously listens for wake word or commands in hands-free mode."""
    print(f"[*] Hands-Free Mode Active. Say '{wake_word}' or give direct commands...")
    
    while True:
        try:
            # Record small window
            wav_path = voice.record_audio(duration_sec=4)
            transcription = voice.transcribe(wav_path).lower().strip()
            
            if not transcription:
                continue
                
            print(f"[Heard]: {transcription}")
            
            # Check if wake word or direct input
            if wake_word in transcription or len(transcription.split()) >= 2:
                # Clean prompt
                command = transcription.replace(wake_word, "").strip()
                if not command:
                    voice.speak("Haan ji, boliye main sun rahi hoon.")
                    # listen for the actual command
                    wav_next = voice.record_audio(duration_sec=6)
                    command = voice.transcribe(wav_next).strip()
                
                if command:
                    print(f"[Processing Command]: {command}")
                    response = agent.process_command(command)
                    voice.speak(response)
                    
        except KeyboardInterrupt:
            print("\nExiting voice listener.")
            break
        except Exception as e:
            print(f"[Loop Error]: {e}")

def main():
    print("==================================================================")
    print("                STARTING NIA DESKTOP AGENT (PHASE 1)              ")
    print("==================================================================")
    
    # 1. Load or initialize configuration
    config = load_config()
    user_name = config["user_profile"]["name"]
    print(f"[+] Loaded Profile: {user_name} | WhatsApp: {config['user_profile']['whatsapp_number']}")
    
    # 2. Initialize Voice & Orchestration Modules
    voice = VoiceEngine(
        tts_voice=config["voice_settings"]["tts_voice"],
        whisper_size=config["voice_settings"]["whisper_model_size"]
    )
    agent = NiaAgentOrchestrator(config)
    
    # Nia Greeting
    greeting = f"Namaste {user_name} ji! Main Nia hoon. Main aapki kya madad kar sakti hoon?"
    voice.speak(greeting)
    
    print("\nSelect Mode:")
    print("1. Interactive Text Mode (Type commands)")
    print("2. Hands-Free Voice Mode (Mic listening)")
    print("3. Both (Voice loop in background + CLI text)")
    
    choice = input("Enter choice (1/2/3) [Default: 1]: ").strip() or "1"
    
    if choice == "2":
        hands_free_voice_loop(agent, voice, config["user_profile"]["wake_word"])
    elif choice == "3":
        voice_thread = threading.Thread(
            target=hands_free_voice_loop,
            args=(agent, voice, config["user_profile"]["wake_word"]),
            daemon=True
        )
        voice_thread.start()
        print("\n[+] Background voice listener running. You can also type commands below.")
        run_cli_loop(agent, voice)
    else:
        run_cli_loop(agent, voice)

def run_cli_loop(agent, voice):
    while True:
        try:
            cmd = input("\nYou > ").strip()
            if cmd.lower() in ("exit", "quit"):
                voice.speak("Alvida! Apna dhyan rakhiyega.")
                break
            if not cmd:
                continue
                
            reply = agent.process_command(cmd)
            print(f"\nNia > {reply}")
            voice.speak(reply)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()


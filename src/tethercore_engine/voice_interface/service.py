# This service will integrate with Whisper.cpp (STT) and Piper/Coqui TTS (TTS).
# Actual integration requires these tools to be installed and accessible,
# potentially as subprocesses or through their Python bindings if available and suitable.

import subprocess # For calling external CLI tools like whisper.cpp or piper
import tempfile # For handling temporary audio files
import os
from typing import Optional, Any

class VoiceInterfaceService:
    """
    Service for handling Speech-to-Text (STT) and Text-to-Speech (TTS) functionalities.
    Integrates with external tools like Whisper.cpp and Piper/Coqui TTS.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initializes the VoiceInterfaceService.
        Args:
            config (dict, optional): Configuration for STT/TTS tools,
                                     e.g., paths to executables, model paths.
        """
        self.config = config or {}
        self.whisper_cpp_path = self.config.get("whisper_cpp_executable", "whisper-cpp") # Assumes in PATH or provide full path
        self.whisper_model_path = self.config.get("whisper_model_path", "models/ggml-base.en.bin") # Example model path

        self.piper_tts_path = self.config.get("piper_tts_executable", "piper") # Assumes in PATH
        self.piper_model_path = self.config.get("piper_tts_model_path") # e.g., "en_US-lessac-medium.onnx"
        self.piper_config_path = self.config.get("piper_tts_config_path") # e.g., "en_US-lessac-medium.onnx.json"

        print("VoiceInterfaceService Initialized (Placeholder for STT/TTS tool integration).")
        if not self.piper_model_path or not self.piper_config_path:
            print("Warning: Piper TTS model or config path not specified. TTS functionality will be limited.")


    async def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        Converts speech from an audio file to text using Whisper.cpp.

        Args:
            audio_file_path (str): Path to the input audio file (e.g., WAV).

        Returns:
            Optional[str]: The transcribed text, or None if an error occurs.
        """
        if not os.path.exists(audio_file_path):
            print(f"Error: Audio file not found at {audio_file_path}")
            return None
        if not os.path.exists(self.whisper_model_path):
            print(f"Error: Whisper model not found at {self.whisper_model_path}")
            return None

        # Command for whisper.cpp (example, adjust based on actual whisper.cpp CLI options)
        # Common options: -m <model_path> -f <file_path> -otxt (output as plain text)
        command = [
            self.whisper_cpp_path,
            "-m", self.whisper_model_path,
            "-f", audio_file_path,
            "-otxt", # Output as plain text to stdout
            "-nt" # No timestamps
        ]
        print(f"VoiceInterface: Running STT command: {' '.join(command)}")

        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            transcribed_text = process.stdout.strip()
            print(f"VoiceInterface: Transcription successful. Text: '{transcribed_text[:100]}...'")
            return transcribed_text
        except FileNotFoundError:
            print(f"Error: Whisper.cpp executable not found at '{self.whisper_cpp_path}'. Please check configuration or PATH.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error during Whisper.cpp execution: {e}")
            print(f"Stderr: {e.stderr}")
            return None
        except Exception as e_gen:
            print(f"An unexpected error occurred during STT: {e_gen}")
            return None

    async def text_to_speech(self, text_to_speak: str, output_audio_file_path: Optional[str] = None) -> Optional[str]:
        """
        Converts text to speech using Piper TTS and saves it to an audio file.

        Args:
            text_to_speak (str): The text to convert to speech.
            output_audio_file_path (Optional[str]): Path to save the output WAV file.
                                                    If None, a temporary file is created and its path returned.

        Returns:
            Optional[str]: Path to the generated audio file, or None if an error occurs.
        """
        if not self.piper_model_path or not self.piper_config_path:
            print("Error: Piper TTS model or config path not set. Cannot perform TTS.")
            return None
        if not os.path.exists(self.piper_model_path):
            print(f"Error: Piper TTS model not found at {self.piper_model_path}")
            return None
        if not os.path.exists(self.piper_config_path):
            print(f"Error: Piper TTS config not found at {self.piper_config_path}")
            return None


        if output_audio_file_path is None:
            # Create a temporary file for the output
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_audio_file_path = temp_file.name
            temp_file.close() # Close it so piper can write to it
            print(f"VoiceInterface: TTS output will be saved to temporary file: {output_audio_file_path}")
        else:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_audio_file_path), exist_ok=True)


        # Command for Piper TTS (example, adjust based on actual Piper CLI options)
        # echo "Hello world." | piper --model <model.onnx> --config <model.onnx.json> --output_file output.wav
        command = f'echo "{text_to_speak.replace("\"", "\\\"")}" | {self.piper_tts_path} --model "{self.piper_model_path}" --config "{self.piper_config_path}" --output_file "{output_audio_file_path}"'

        print(f"VoiceInterface: Running TTS command: {command}")

        try:
            # Using shell=True here because of the pipe. Be cautious with shell=True if text_to_speak is user-supplied directly without sanitization.
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, encoding='utf-8')
            if process.stderr: # Piper might output info to stderr
                print(f"Piper TTS stderr: {process.stderr.strip()}")
            if os.path.exists(output_audio_file_path) and os.path.getsize(output_audio_file_path) > 0:
                print(f"VoiceInterface: TTS successful. Audio saved to: {output_audio_file_path}")
                return output_audio_file_path
            else:
                print(f"Error: TTS output file not created or is empty at {output_audio_file_path}")
                print(f"Stdout: {process.stdout}")
                print(f"Stderr: {process.stderr}")
                if os.path.exists(output_audio_file_path) and output_audio_file_path.startswith(tempfile.gettempdir()):
                    os.remove(output_audio_file_path) # Clean up temp file on failure
                return None

        except FileNotFoundError:
            print(f"Error: Piper TTS executable not found at '{self.piper_tts_path}'. Please check configuration or PATH.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error during Piper TTS execution: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            if os.path.exists(output_audio_file_path) and output_audio_file_path.startswith(tempfile.gettempdir()):
                os.remove(output_audio_file_path) # Clean up temp file
            return None
        except Exception as e_gen:
            print(f"An unexpected error occurred during TTS: {e_gen}")
            if os.path.exists(output_audio_file_path) and output_audio_file_path.startswith(tempfile.gettempdir()):
                os.remove(output_audio_file_path) # Clean up temp file
            return None

    async def play_audio_file(self, audio_file_path: str):
        """
        Plays an audio file using a system's default player.
        This is platform-dependent and very basic.
        Args:
            audio_file_path (str): Path to the audio file to play.
        """
        if not os.path.exists(audio_file_path):
            print(f"Cannot play audio: file not found at {audio_file_path}")
            return

        print(f"VoiceInterface: Attempting to play audio file: {audio_file_path} (platform-dependent)")
        try:
            if os.name == 'nt': # Windows
                os.startfile(audio_file_path)
            elif os.uname().sysname == 'Darwin': # macOS
                subprocess.call(['open', audio_file_path])
            else: # Linux and other POSIX
                subprocess.call(['xdg-open', audio_file_path])
        except Exception as e:
            print(f"Could not play audio file {audio_file_path}: {e}")
            print("Ensure you have a default media player configured for WAV files.")


# Example Usage
if __name__ == "__main__":
    # Create dummy audio file for STT testing
    # This requires 'sox' or 'ffmpeg' to be installed to generate a test wav
    # For simplicity, assume a test.wav exists or manually create one.
    # Example: sox -n -r 16000 -c 1 test.wav synth 2 sine 440 gain -10
    
    # Ensure you have whisper.cpp and its models, and Piper TTS and its models downloaded
    # and paths configured correctly in `config` or directly in the class for this example.
    example_config = {
        "whisper_cpp_executable": "main", # Path to your whisper.cpp main executable
        "whisper_model_path": "models/ggml-base.en.bin", # Path to your whisper model
        "piper_tts_executable": "piper", # Path to your piper executable
        "piper_tts_model_path": "models/en_US-lessac-medium.onnx", # Path to piper voice model
        "piper_tts_config_path": "models/en_US-lessac-medium.onnx.json" # Path to piper voice config
    }
    # Create dummy model files for the example to run without actual tools
    os.makedirs("models", exist_ok=True)
    # with open(example_config["whisper_model_path"], "w") as f: f.write("dummy whisper model")
    # with open(example_config["piper_tts_model_path"], "w") as f: f.write("dummy piper model")
    # with open(example_config["piper_tts_config_path"], "w") as f: f.write("{}") # Dummy JSON config
    # with open("test_audio.wav", "w") as f: f.write("dummy audio data") # Dummy audio

    async def main():
        voice_service = VoiceInterfaceService(config=example_config)

        # --- Test TTS ---
        text_to_say = "Hello from TetherCore's voice interface."
        output_wav_path = await voice_service.text_to_speech(text_to_say, "test_output.wav")

        if output_wav_path:
            print(f"TTS output saved to: {output_wav_path}")
            # await voice_service.play_audio_file(output_wav_path) # Uncomment to try playing
            # For testing STT, we'd need a real audio file.
            # For now, we'll just clean up the generated TTS file if it exists.
            # if os.path.exists(output_wav_path):
            #     os.remove(output_wav_path)
        else:
            print("TTS failed.")

        # --- Test STT (requires a real audio file and whisper.cpp setup) ---
        # print("\n--- Testing STT ---")
        # # Create a dummy test_audio.wav if you don't have one
        # # This is just a placeholder. You need a real WAV file.
        # if not os.path.exists("test_audio.wav"):
        #     print("Please create a 'test_audio.wav' file in the project root for STT testing.")
        # else:
        #     transcription = await voice_service.speech_to_text("test_audio.wav")
        #     if transcription:
        #         print(f"STT Transcription: {transcription}")
        #     else:
        #         print("STT failed.")
        
        # Clean up dummy files if they were created by this script
        # if os.path.exists("test_audio.wav") and open("test_audio.wav").read() == "dummy audio data":
        #     os.remove("test_audio.wav")

    # import asyncio
    # asyncio.run(main()) # Commented out
    pass

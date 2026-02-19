import io
import os
import logging
import tempfile
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# Create uploads directory for temporary audio files
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_extension(filename: str, content_type: Optional[str]) -> str:
    """Determine file extension from filename or content_type."""
    extension = "webm"
    
    if filename and "." in filename:
        extension = filename.rsplit(".", 1)[-1].lower()
    elif content_type:
        if "ogg" in content_type:
            extension = "ogg"
        elif "wav" in content_type:
            extension = "wav"
        elif "mp3" in content_type or "mpeg" in content_type:
            extension = "mp3"
        elif "webm" in content_type:
            extension = "webm"
    
    return extension


def _convert_to_wav_file(audio_bytes: bytes, extension: str) -> str:
    """
    Convert audio to WAV format using ffmpeg directly.
    Returns path to the WAV file.
    """
    import time
    import subprocess
    import shutil
    
    timestamp = int(time.time() * 1000)
    
    # Save input audio to file
    src_path = os.path.join(UPLOAD_DIR, f"input_{timestamp}.{extension}")
    wav_path = os.path.join(UPLOAD_DIR, f"output_{timestamp}.wav")
    
    with open(src_path, "wb") as f:
        f.write(audio_bytes)
    
    logger.info(f"Saved input audio to {src_path} ({len(audio_bytes)} bytes)")
    
    # Check if ffmpeg is available
    if not shutil.which("ffmpeg"):
        logger.error("ffmpeg not found on PATH!")
        raise RuntimeError("ffmpeg is required for audio conversion but was not found on PATH.")
    
    try:
        logger.info(f"Converting {extension} to wav using ffmpeg...")
        
        # Run ffmpeg to convert to 16kHz mono WAV
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",              # Overwrite output
                "-i", src_path,    # Input file
                "-ac", "1",        # Mono
                "-ar", "16000",    # 16kHz sample rate
                "-f", "wav",       # Output format
                wav_path           # Output file
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
        
        logger.info(f"Converted to WAV: {wav_path}")
        
        # Cleanup source file
        try:
            os.unlink(src_path)
        except OSError:
            pass
        
        return wav_path
        
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg conversion timed out")
        raise RuntimeError("Audio conversion timed out")
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        # Cleanup on error
        for path in (src_path, wav_path):
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass
        raise RuntimeError(f"Failed to convert audio to WAV: {e}")


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm", content_type: Optional[str] = None) -> dict:
    """
    Transcribe audio using the ASR API.
    
    Converts webm/ogg to WAV file on disk before sending since ASR works best with wav/mp3.
    
    Args:
        audio_bytes: Raw audio data
        filename: Original filename (used to detect format)
        content_type: MIME type of the audio
        
    Returns:
        dict with keys: transcript, status, language, note
    """
    import time
    asr_url = os.getenv("ASR_URL", "http://localhost:8002")
    
    extension = _get_extension(filename, content_type)
    
    logger.info(f"Transcribing audio: {len(audio_bytes)} bytes, ext={extension}")
    
    wav_path = None
    try:
        # Convert to WAV file if not already wav or mp3
        if extension not in ("wav", "mp3"):
            wav_path = _convert_to_wav_file(audio_bytes, extension)
            upload_mime = "audio/wav"
        else:
            # Save directly to file
            timestamp = int(time.time() * 1000)
            wav_path = os.path.join(UPLOAD_DIR, f"input_{timestamp}.{extension}")
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)
            upload_mime = "audio/wav" if extension == "wav" else "audio/mpeg"
        
        logger.info(f"Audio file ready at: {wav_path}")
        
        # Send to LexEdge ASR with retries
        last_error = None
        for attempt in range(2):
            try:
                logger.info(f"ASR request attempt {attempt + 1} to {asr_url}/transcribe")
                
                # Open file fresh for each attempt
                with open(wav_path, "rb") as audio_file:
                    files = {
                        "file": (os.path.basename(wav_path), audio_file, upload_mime)
                    }
                    response = requests.post(
                        f"{asr_url}/transcribe",
                        files=files,
                        headers={"accept": "application/json"},
                        timeout=90
                    )
                
                logger.info(f"ASR response status: {response.status_code}")
                
                if response.status_code >= 500:
                    last_error = RuntimeError(f"ASR server error: {response.text}")
                    logger.warning(f"ASR server error (attempt {attempt + 1}): {response.text}")
                    continue
                    
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"ASR success: status={result.get('status')}, transcript_len={len(result.get('transcript', ''))}")
                
                # Clean up transcript (remove special tokens like </s>)
                if result.get("transcript"):
                    result["transcript"] = result["transcript"].replace("</s>", "").replace("<s>", "").strip()
                
                return result
                
            except requests.exceptions.Timeout:
                last_error = RuntimeError("ASR request timed out")
                logger.warning(f"ASR timeout (attempt {attempt + 1})")
            except requests.exceptions.RequestException as exc:
                last_error = exc
                logger.warning(f"ASR request error (attempt {attempt + 1}): {exc}")
            except Exception as exc:
                last_error = exc
                logger.error(f"Unexpected error during transcription: {exc}")

        error_msg = f"ASR transcription failed after retries: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    finally:
        # Cleanup temp file
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
                logger.info(f"Cleaned up temp file: {wav_path}")
            except OSError:
                pass

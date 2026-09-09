import io
import json
import numpy as np
import streamlit as st

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    import librosa
    import soundfile as sf
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


@st.cache_resource
def load_voice_encoder():
    if not VOICE_AVAILABLE:
        return None
    try:
        return VoiceEncoder()
    except Exception as e:
        st.error(f"Failed to load voice encoder: {e}")
        return None


def _decode_audio(audio_bytes):
    if not audio_bytes:
        return None, 16000
    try:
        audio, sr = sf.read(io.BytesIO(audio_bytes))
    except Exception:
        try:
            audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        except Exception:
            return None, 16000

    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    return audio.astype(np.float32), sr


def get_voice_embedding(audio_bytes):
    if not VOICE_AVAILABLE or not audio_bytes:
        return None
    try:
        encoder = load_voice_encoder()
        if encoder is None:
            return None

        audio, sr = _decode_audio(audio_bytes)
        if audio is None or len(audio) == 0:
            return None

        wav = preprocess_wav(audio, source_sr=sr)
        if len(wav) == 0:
            # Fallback if VAD trimmed everything (e.g. quiet audio)
            wav = librosa.resample(audio, orig_sr=sr, target_sr=16000) if sr != 16000 else audio

        embedding = encoder.embed_utterance(wav)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()
    except Exception as e:
        print(f"Voice embedding error: {e}")
        return None


def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    new_vec = np.array(new_embedding, dtype=np.float32)
    norm_new = np.linalg.norm(new_vec)
    if norm_new > 0:
        new_vec = new_vec / norm_new

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if not stored_embedding:
            continue
        if isinstance(stored_embedding, str):
            try:
                stored_embedding = json.loads(stored_embedding)
            except Exception:
                continue
        try:
            stored_vec = np.array(stored_embedding, dtype=np.float32)
            norm_stored = np.linalg.norm(stored_vec)
            if norm_stored > 0:
                stored_vec = stored_vec / norm_stored

            similarity = float(np.dot(new_vec, stored_vec))
            if similarity > best_score:
                best_score = similarity
                best_sid = sid
        except Exception:
            continue

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    if not VOICE_AVAILABLE or not audio_bytes or not candidates_dict:
        return {}

    try:
        encoder = load_voice_encoder()
        if encoder is None:
            return {}

        audio, sr = _decode_audio(audio_bytes)
        if audio is None or len(audio) == 0:
            return {}

        # Split audio into speech chunks based on silence
        try:
            segments = librosa.effects.split(audio, top_db=30)
        except Exception:
            segments = [[0, len(audio)]]

        if len(segments) == 0:
            segments = [[0, len(audio)]]

        identified_results = {}

        for start, end in segments:
            if (end - start) < sr * 0.4:
                continue
            segment_audio = audio[start:end]
            try:
                wav = preprocess_wav(segment_audio, source_sr=sr)
            except Exception:
                wav = segment_audio
            if len(wav) == 0:
                continue

            embedding = encoder.embed_utterance(wav)
            sid, score = identify_speaker(embedding, candidates_dict, threshold)
            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results
    except Exception as e:
        print(f"Bulk voice processing error: {e}")
        return {}
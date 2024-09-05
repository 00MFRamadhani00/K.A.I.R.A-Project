import os
import torch
import requests
import urllib.parse
import torchaudio  # Import torchaudio

# Dalam perbaikan
def silero_tts(text, speaker='en_1', filename="test.wav"):
    device = torch.device('cpu')
    torch.set_num_threads(4)
    local_file = 'model.pt'

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file(f'https://models.silero.ai/models/tts/en/v3_en.pt', local_file)  

    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    sample_rate = 24000  # Change this to a valid sample rate: 8000, 24000, or 48000

    audio = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
    
    # Ensure the audio tensor is properly converted to byte format and saved as a WAV file
    torchaudio.save(filename, audio.unsqueeze(0), sample_rate)

def voicevox_tts(tts, filename="test.wav"):
    voicevox_url = 'http://localhost:50021'
    params_encoded = urllib.parse.urlencode({'text': tts, 'speaker': 58})
    request = requests.post(f'{voicevox_url}/audio_query?{params_encoded}')
    params_encoded = urllib.parse.urlencode({'speaker': 58, 'enable_interrogative_upspeak': True})
    request = requests.post(f'{voicevox_url}/synthesis?{params_encoded}', json=request.json())

    with open(filename, "wb") as outfile:
        outfile.write(request.content)
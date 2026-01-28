# Azure Speech Services Setup

## Environment Variables

Add the following to your `.env` file:

```
AZURE_SPEECH_KEY=your-azure-speech-api-key
AZURE_SPEECH_REGION=your-azure-region
# Optional: If you have a custom endpoint
AZURE_SPEECH_ENDPOINT=https://your-speech-resource.cognitiveservices.azure.com/
```

## Getting Azure Speech Services Credentials

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a new "Speech" resource or use an existing one
3. Go to "Keys and Endpoint" section
4. Copy one of the "Keys" and the "Location/Region"
5. Add them to your `.env` file

## Common Azure Regions

- `eastus` - East US
- `westus` - West US
- `westus2` - West US 2
- `eastasia` - East Asia
- `southeastasia` - Southeast Asia
- `northeurope` - North Europe
- `westeurope` - West Europe

## Installation

The Azure Speech Services package is already in `requirements.txt`:
```
azure-cognitiveservices-speech
```

Install it with:
```bash
pip install azure-cognitiveservices-speech
```

## How It Works

- **Audio Sample Upload**: When a user uploads an audio sample, the file path is stored for verification
- **Audio Verification**: During the interview, audio clips are captured every 5 seconds and compared with the stored sample using:
  - Azure Speech Services for transcription (if needed)
  - Audio feature comparison (MFCC) for voice verification
- **Voice Matching**: Uses cosine similarity of MFCC features to verify if the voice matches the stored sample

## Notes

- Audio verification uses MFCC (Mel-frequency cepstral coefficients) features for voice matching
- The system converts audio to WAV format for Azure Speech Services compatibility
- If Azure Speech Services is not configured, the system gracefully degrades and allows verification


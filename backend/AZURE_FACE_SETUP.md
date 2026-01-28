# Azure Face API Setup

## Environment Variables

Add the following to your `.env` file:

```
AZURE_FACE_ENDPOINT=https://your-face-api-resource.cognitiveservices.azure.com/
AZURE_FACE_KEY=your-azure-face-api-key
```

## Getting Azure Face API Credentials

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a new "Face" resource or use an existing one
3. Go to "Keys and Endpoint" section
4. Copy the "Endpoint" and one of the "Keys"
5. Add them to your `.env` file

## Installation

The Azure Face API package is already in `requirements.txt`:
```
azure-cognitiveservices-vision-face
msrest
```

Install it with:
```bash
pip install azure-cognitiveservices-vision-face msrest
```

## How It Works

- **Photo Upload**: When a user uploads a photo, Azure Face API detects the face and returns a Face ID (GUID)
- **Face Verification**: During the interview, snapshots are compared with the stored Face ID using Azure's verify API
- **Confidence Threshold**: Faces are considered matching if confidence >= 0.6 (60%)

## Notes

- Azure Face IDs expire after 24 hours, so users need to re-upload samples if they start an interview after that period
- The service gracefully handles missing credentials by bypassing face verification
- Face detection uses Azure's `detection_01` model (can be changed to `detection_02` or `detection_03` for better accuracy)


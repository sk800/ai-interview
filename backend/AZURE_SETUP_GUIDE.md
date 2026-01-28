# Azure Face API Setup Guide for Face Monitoring

## What Azure Resource You Need

### 1. **Azure AI Services - Face API Resource**

You need to create a **Face API resource** (not Computer Vision) in Azure. Here's how:

#### Step-by-Step Setup:

1. **Go to Azure Portal**: https://portal.azure.com

2. **Create a Face API Resource**:
   - Click "Create a resource"
   - Search for "Face" or "Azure AI Services"
   - Select **"Face"** (not Computer Vision)
   - Click "Create"

3. **Configure the Resource**:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose a region (e.g., East US, West Europe)
   - **Name**: Give it a name (e.g., "my-face-api")
   - **Pricing Tier**: 
     - **F0 (Free)**: 20 calls/minute, 30,000 calls/month
     - **S0 (Standard)**: More calls, pay-as-you-go
   - Click "Review + create" then "Create"

4. **Get Your Credentials**:
   - After creation, go to your resource
   - Click "Keys and Endpoint" in the left menu
   - Copy:
     - **Endpoint**: `https://your-resource-name.cognitiveservices.azure.com/`
     - **Key 1** or **Key 2**: Your subscription key

5. **Add to .env file**:
   ```
   AZURE_FACE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
   AZURE_FACE_KEY=your-key-here
   ```

## Important Notes

### What Works WITHOUT Identification/Verification Features:
✅ **Face Detection** - Detect faces in images
✅ **Face Attributes** - Age, gender, emotion, head pose
✅ **Face Rectangle** - Position and size of face
✅ **Basic Monitoring** - Detect if face is present or not

### What Requires Identification/Verification Features (Requires Approval):
❌ **Face ID** - Unique identifier for each face
❌ **Face Verification** - Compare two faces directly
❌ **Face Identification** - Identify a person from a group
❌ **Person Groups** - Store multiple faces for one person

### To Enable Identification/Verification Features:
1. Go to: https://aka.ms/facerecognition
2. Fill out the application form
3. Wait for approval (usually 24-48 hours)
4. Once approved, you can use `returnFaceId=True`

## Current Implementation

The current code uses **attribute-based comparison** which works without Identification/Verification features:
- Detects face presence
- Extracts face attributes (age, gender, head pose)
- Compares attributes between stored and live images
- Sends alerts based on similarity scores

## Troubleshooting

### If you get "InvalidRequest" error:
1. Check your endpoint format: Should be `https://your-resource.cognitiveservices.azure.com/`
2. Check your key: Should be 32 characters
3. Verify the resource is "Face API" not "Computer Vision"
4. Make sure the resource is in a supported region

### If face detection doesn't work:
1. Verify image format: JPEG, PNG, BMP, or GIF
2. Check image size: Should be less than 4MB
3. Ensure face is clearly visible
4. Check lighting conditions

## Alternative: Use REST API Directly

If the SDK continues to have issues, the code now falls back to using REST API directly, which is more reliable.


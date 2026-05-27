# CIRCVIS API Documentation - For Frontend Integration

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Single Image Prediction
**POST** `/api/predict`

Upload a single image file.

**Request:**
```bash
curl -X POST -F "file=@image.jpg" http://localhost:8000/api/predict
```

**Request Body:**
- `file` (required): Image file (JPEG, PNG, etc.)

**Response:**
```json
{
  "class_name": "Plastic",
  "confidence": 0.9999,
  "all_classes": {
    "Plastic": 0.9999,
    "Organic": 0.00001,
    "Metal": 0.00001,
    "Paper/Cardboard": 0.00001,
    "Glass": 0.00001,
    "Textile": 0.00001,
    "Miscellaneous": 0.00001
  },
  "processing_time_ms": 95.3
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid image file
- `503`: Model not loaded

---

### 2. Base64 Image Prediction
**POST** `/api/predict-base64`

Predict from base64-encoded image string.

**Request:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"image":"iVBORw0KGgoAAAAN..."}' \
  http://localhost:8000/api/predict-base64
```

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response:** Same as single prediction

---

### 3. Batch Prediction
**POST** `/api/predict-batch`

Predict multiple images at once.

**Request:**
```bash
curl -X POST -F "files=@img1.jpg" -F "files=@img2.jpg" -F "files=@img3.jpg" \
  http://localhost:8000/api/predict-batch
```

**Request Body:**
- `files` (required, multiple): Multiple image files

**Response:**
```json
{
  "predictions": [
    {
      "class_name": "Plastic",
      "confidence": 0.9999,
      "all_classes": {...},
      "processing_time_ms": 95.3,
      "filename": "img1.jpg"
    },
    {
      "class_name": "Metal",
      "confidence": 0.98,
      "all_classes": {...},
      "processing_time_ms": 90.1,
      "filename": "img2.jpg"
    }
  ],
  "total": 2
}
```

---

### 4. URL Image Prediction
**POST** `/api/predict-url`

Predict image from URL.

**Request:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/image.jpg"}' \
  http://localhost:8000/api/predict-url
```

**Request Body:**
```json
{
  "url": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "class_name": "Plastic",
  "confidence": 0.9999,
  "all_classes": {...},
  "processing_time_ms": 95.3,
  "source_url": "https://example.com/image.jpg"
}
```

---

### 5. Get Available Models
**GET** `/api/models`

Get list of loaded models and status.

**Request:**
```bash
curl http://localhost:8000/api/models
```

**Response:**
```json
{
  "models": ["circvis"],
  "ready": true,
  "accuracy": 85,
  "model_name": "CIRCVIS Model",
  "calibration_version": "2.2"
}
```

---

### 6. Health Check
**GET** `/health`

Check server and model status.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "models_loaded": true,
  "model_names": ["circvis"],
  "model_file_exists": true,
  "inference_version": "2.2",
  "api": "/api/predict"
}
```

---

## Frontend Examples

### HTML Form Upload
```html
<!DOCTYPE html>
<html>
<head>
    <title>CIRCVIS Prediction</title>
</head>
<body>
    <input type="file" id="fileInput" accept="image/*">
    <button onclick="uploadImage()">Predict</button>
    <div id="result"></div>

    <script>
        async function uploadImage() {
            const file = document.getElementById('fileInput').files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML = `
                    <h2>${result.class_name}</h2>
                    <p>Confidence: ${(result.confidence * 100).toFixed(2)}%</p>
                    <p>Time: ${result.processing_time_ms.toFixed(1)}ms</p>
                `;
            } catch (error) {
                console.error('Prediction error:', error);
            }
        }
    </script>
</body>
</html>
```

### Live Camera Feed
```html
<!DOCTYPE html>
<html>
<head>
    <title>CIRCVIS Live Camera</title>
</head>
<body>
    <video id="video" width="640" height="480" autoplay></video>
    <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>
    <div id="result"></div>

    <script>
        let videoStream;
        
        async function startCamera() {
            videoStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            document.getElementById('video').srcObject = videoStream;
            
            // Predict every 2 seconds
            setInterval(captureAndPredict, 2000);
        }
        
        async function captureAndPredict() {
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const video = document.getElementById('video');
            
            ctx.drawImage(video, 0, 0, 640, 480);
            
            // Convert canvas to blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('file', blob, 'frame.jpg');
                
                try {
                    const response = await fetch('/api/predict', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = `
                        <h2>${result.class_name}</h2>
                        <p>Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
                        <p>Time: ${result.processing_time_ms.toFixed(1)}ms</p>
                    `;
                } catch (error) {
                    console.error('Prediction error:', error);
                }
            }, 'image/jpeg', 0.95);
        }
        
        startCamera();
    </script>
</body>
</html>
```

### React Component Example
```jsx
import React, { useState } from 'react';

function PredictionComponent() {
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            setPrediction(result);
        } catch (error) {
            console.error('Prediction error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileUpload}
            />
            {loading && <p>Loading...</p>}
            {prediction && (
                <div>
                    <h2>{prediction.class_name}</h2>
                    <p>Confidence: {(prediction.confidence * 100).toFixed(2)}%</p>
                    <p>Time: {prediction.processing_time_ms.toFixed(1)}ms</p>
                </div>
            )}
        </div>
    );
}

export default PredictionComponent;
```

### Vue.js Component Example
```vue
<template>
    <div>
        <input type="file" @change="handleFileUpload" accept="image/*">
        <div v-if="loading">Loading...</div>
        <div v-if="prediction">
            <h2>{{ prediction.class_name }}</h2>
            <p>Confidence: {{ (prediction.confidence * 100).toFixed(2) }}%</p>
            <p>Time: {{ prediction.processing_time_ms.toFixed(1) }}ms</p>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            prediction: null,
            loading: false
        };
    },
    methods: {
        async handleFileUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            this.loading = true;
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    body: formData
                });
                this.prediction = await response.json();
            } catch (error) {
                console.error('Prediction error:', error);
            } finally {
                this.loading = false;
            }
        }
    }
};
</script>
```

---

## Error Handling

### Handle Different HTTP Codes
```javascript
async function predict(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            if (response.status === 400) {
                console.error('Invalid image file');
            } else if (response.status === 503) {
                console.error('Model not loaded. Run training first.');
            } else {
                console.error(`Server error: ${response.status}`);
            }
            return null;
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}
```

---

## Response Schema

### Waste Classes
The `class_name` field will be one of:
- `Plastic`
- `Organic`
- `Metal`
- `Paper/Cardboard`
- `Glass`
- `Textile`
- `Miscellaneous`

### Confidence Ranges
- `0.0 - 1.0` (multiply by 100 for percentage)
- Higher values = more confident
- `0.95+` = Very confident
- `0.80-0.95` = Confident
- `0.50-0.80` = Less confident
- `<0.50` = Low confidence (may be wrong class)

### All Classes Object
Contains predictions for all waste categories:
```json
"all_classes": {
  "Plastic": 0.9999,
  "Organic": 0.00001,
  "Metal": 0.00001,
  "Paper/Cardboard": 0.00001,
  "Glass": 0.00001,
  "Textile": 0.00001,
  "Miscellaneous": 0.00001
}
```

Sum of all values = 1.0 (probabilities)

---

## Performance Tips

1. **First prediction is slower** - Model needs to load
   - Subsequent predictions: 80-120ms
   - First prediction: 500-1000ms

2. **Batch predictions are faster**
   - Single: ~95ms each
   - Batch of 5: ~18ms each average

3. **Optimize image size**
   - Recommended: 1000-2000px
   - Very large (4K): 100-150ms
   - Small (480p): 70-90ms

4. **Use compression**
   - JPEG quality 90-95 works well
   - Reduces file size, minimal quality loss

---

## Common Issues

### "Model not loaded"
**Solution**: Run `python data/finetune_model.py` to train model

### "Invalid image file"
**Solution**: Ensure file is valid JPEG/PNG, not corrupted

### Slow predictions
**Solution**: Check GPU is available or use smaller images

### Wrong predictions
**Solution**: See `improve_accuracy.py` or retrain model

---

## Testing

### Test Prediction
```bash
curl -X POST -F "file=@test_image.jpg" http://localhost:8000/api/predict
```

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Batch
```bash
curl -X POST -F "files=@img1.jpg" -F "files=@img2.jpg" http://localhost:8000/api/predict-batch
```

---

## Support

For issues or questions:
1. Check logs in `training_log.txt` and `finetune_log.txt`
2. Run `python test_predictions.py` for diagnostics
3. See `MODEL_FIX_SUMMARY.md` for technical details

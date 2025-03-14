import re
import numpy as np
import json

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

def convert_numpy(obj):
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    return obj

def normalize_emotions(emotion_dict):
    total = sum(emotion_dict.values())
    if total > 0:
        return {emotion: (value / total) * 100 for emotion, value in emotion_dict.items()}
    return emotion_dict
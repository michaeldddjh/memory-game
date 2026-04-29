import cv2
import numpy as np
import os, base64
from collections import Counter

# Stricter face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

photos = [
    "/Users/michael/Downloads/WeChat/IMG_7060.JPG",
    "/Users/michael/Downloads/WeChat/IMG_7061.JPG",
    "/Users/michael/Downloads/WeChat/IMG_7062.JPG",
    "/Users/michael/Downloads/WeChat/IMG_7063.JPG",
    "/Users/michael/Downloads/WeChat/IMG_7064.JPG",
]

os.makedirs("portraits_db", exist_ok=True)

all_faces = []

for pi, photo_path in enumerate(photos):
    img = cv2.imread(photo_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Use stricter detection parameters
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.08,   # tighter scale
        minNeighbors=8,     # much stricter (was 4-5)
        minSize=(60, 60),   # larger minimum
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    print(f"\nPhoto {pi+1}: {os.path.basename(photo_path)} ({img.shape[1]}x{img.shape[0]})")
    print(f"   Raw detections: {len(faces)}")
    
    for i, (x, y, w, h) in enumerate(faces):
        # Aspect ratio check - faces should be roughly square or taller
        ratio = w / h
        if ratio > 1.3 or ratio < 0.6:
            print(f"   X Face {i}: BAD RATIO {ratio:.2f} at ({x},{y},{w},{h})")
            continue
        
        # Size check - reject tiny faces
        if w < 70 or h < 70:
            print(f"   X Face {i}: TOO SMALL ({w}x{h}) at ({x},{y})")
            continue
            
        # Check for eyes in the face region (top 60% only)
        face_top = gray[y:y+int(h*0.6), x:x+w]
        eyes = eye_cascade.detectMultiScale(face_top, scaleFactor=1.1, minNeighbors=5, minSize=(15,15))
        
        # Need at least 2 eyes
        if len(eyes) < 2:
            print(f"   X Face {i}: ONLY {len(eyes)} EYE(S) at ({x},{y},{w},{h})")
            continue
            
        # Skin color check - sample center of face
        face_roi = img[y:y+h, x:x+w]
        cx, cy = w//2, h//2
        sample_size = min(w, h) // 4
        center_sample = face_roi[cy-sample_size:cy+sample_size, cx-sample_size:cx+sample_size]
        
        hsv = cv2.cvtColor(center_sample, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 30, 60])
        upper_skin = np.array([25, 180, 255])
        lower_skin2 = np.array([170, 30, 60])
        upper_skin2 = np.array([180, 180, 255])
        
        mask1 = cv2.inRange(hsv, lower_skin, upper_skin)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        skin_ratio = (np.sum(mask1) + np.sum(mask2)) / (center_sample.size)
        
        if skin_ratio < 0.25:
            print(f"   X Face {i}: LOW SKIN {skin_ratio:.2f} at ({x},{y},{w},{h})")
            continue
        
        # Additional check: variance of face region (real faces have high variance, walls don't)
        face_gray = gray[y:y+h, x:x+w]
        variance = np.var(face_gray)
        if variance < 300:
            print(f"   X Face {i}: LOW VARIANCE {variance:.0f} at ({x},{y},{w},{h}) - likely flat surface")
            continue
        
        # Eye vertical position check - eyes should be in upper 55% of face
        eye_positions = []
        for (ex, ey, ew, eh) in eyes:
            eye_rel_y = (y + ey + eh//2) - y
            eye_positions.append(eye_rel_y / h)
        
        avg_eye_y = np.mean(eye_positions)
        if avg_eye_y > 0.6:
            print(f"   X Face {i}: EYES TOO LOW (y={avg_eye_y:.2f}) at ({x},{y},{w},{h})")
            continue
        
        print(f"   OK Face {i}: ratio={ratio:.2f} skin={skin_ratio:.2f} eyes={len(eyes)} var={variance:.0f} eyeY={avg_eye_y:.2f} at ({x},{y},{w},{h})")
        all_faces.append((pi, x, y, w, h, len(eyes), skin_ratio, variance))

print(f"\n{'='*60}")
print(f"Total valid faces: {len(all_faces)}")
print(f"   By photo: ", end="")
by_photo = Counter(f[0] for f in all_faces)
for p in sorted(by_photo.keys()):
    print(f"P{p+1}={by_photo[p]}", end="  ")
print()

# Select top 18 by quality score
scored = []
for pi, x, y, w, h, neyes, skin, var in all_faces:
    size_score = w * h / 1000
    score = size_score + skin * 100 + min(var/100, 20)
    scored.append((score, pi, x, y, w, h))

scored.sort(reverse=True)

# Select up to 18, ensuring no heavy overlap
selected = []
for score, pi, x, y, w, h in scored:
    overlap = False
    for _, spi, sx, sy, sw, sh in selected:
        x1 = max(x, sx)
        y1 = max(y, sy)
        x2 = min(x+w, sx+sw)
        y2 = min(y+h, sy+sh)
        if x2 > x1 and y2 > y1:
            inter = (x2-x1)*(y2-y1)
            area1 = w*h
            area2 = sw*sh
            iou = inter / min(area1, area2)
            if iou > 0.3:
                overlap = True
                break
    if not overlap:
        selected.append((score, pi, x, y, w, h))
    if len(selected) >= 18:
        break

print(f"\nSelected {len(selected)} faces:")
for i, (score, pi, x, y, w, h) in enumerate(selected):
    print(f"   {i+1}. Photo{pi+1} ({x},{y},{w}x{h}) score={score:.0f}")

# Crop faces as SQUARE
print(f"\nCropping square portraits...")
avatars = []
for i, (score, pi, x, y, w, h) in enumerate(selected):
    img = cv2.imread(photos[pi])
    
    # Make square: use the larger dimension, center the crop
    size = max(w, h)
    # Expand by 30% for some context
    size = int(size * 1.3)
    cx, cy = x + w//2, y + h//2
    
    # Square crop coordinates
    x1 = max(0, cx - size//2)
    y1 = max(0, cy - size//2)
    x2 = min(img.shape[1], x1 + size)
    y2 = min(img.shape[0], y1 + size)
    # Adjust if out of bounds
    if x2 - x1 < size:
        x1 = max(0, x2 - size)
    if y2 - y1 < size:
        y1 = max(0, y2 - size)
    
    crop = img[y1:y2, x1:x2]
    
    # Resize to 200x200 for web
    crop = cv2.resize(crop, (200, 200), interpolation=cv2.INTER_AREA)
    
    # Save to portraits_db
    cv2.imwrite(f"portraits_db/portrait_{i:02d}.jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 80])
    
    # Base64 encode
    _, buf = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 75])
    b64 = base64.b64encode(buf).decode()
    avatars.append(b64)
    print(f"   {i+1}. Photo{pi+1} -> portrait_{i:02d}.jpg ({size}x{size} -> 200x200, {len(b64)} chars)")

# Save base64 data for game
with open("avatars_data.py", "w") as f:
    f.write("AVATARS = [\n")
    for b64 in avatars:
        f.write(f'  "data:image/jpeg;base64,{b64}",\n')
    f.write("]\n")

print(f"\nSaved {len(avatars)} portraits to portraits_db/ and avatars_data.py")
print(f"   Total base64 size: {sum(len(a) for a in avatars)} chars")

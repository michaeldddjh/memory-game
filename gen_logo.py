import json
import urllib.request
import base64
import os

api_key = "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"

models = [
    "google/gemini-2.5-flash-preview-image-generation",
]

prompt = "Generate an elegant card back design for a memory card game. Dark navy blue background with ornate gold border, baroque scrollwork decorations. The Chinese characters 大麦 should be subtly integrated into the center decorative pattern like a watermark - not too prominent. Symmetric design, 512x512 pixels. Make the 大麦 characters look like they belong naturally in the ornamental design."

for model in models:
    try:
        print(f"Trying model: {model}")
        
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode('utf-8'))
        
        print(f"Response keys: {list(result.keys())}")
        
        if 'choices' in result:
            for choice in result['choices']:
                msg = choice.get('message', {})
                content = msg.get('content', '')
                
                if isinstance(content, list):
                    for i, part in enumerate(content):
                        if isinstance(part, dict):
                            ptype = part.get('type', 'unknown')
                            print(f"  Part {i}: type={ptype}")
                            if ptype == 'image_url':
                                img_url = part.get('image_url', {}).get('url', '')
                                if img_url.startswith('data:'):
                                    img_data = img_url.split(',')[1]
                                    out_path = '/Users/michael/projects/memory-game/card-back-logo.png'
                                    with open(out_path, 'wb') as f:
                                        f.write(base64.b64decode(img_data))
                                    print(f"  Saved! {os.path.getsize(out_path)} bytes")
                                else:
                                    out_path = '/Users/michael/projects/memory-game/card-back-logo.png'
                                    urllib.request.urlretrieve(img_url, out_path)
                                    print(f"  Downloaded from URL!")
                            elif ptype == 'text':
                                print(f"  Text: {part.get('text', '')[:200]}")
                elif isinstance(content, str):
                    print(f"  Text: {content[:500]}")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
            
    except Exception as e:
        print(f"Failed: {e}")

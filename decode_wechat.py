import os

msg_dir = "/Users/michael/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_9hyqz836ej7522_887d/msg/img"

# Get recent .dat files sorted by modification time
dat_files = []
for root, dirs, files in os.walk(msg_dir):
    for f in files:
        if f.endswith('.dat'):
            full = os.path.join(root, f)
            stat = os.stat(full)
            if stat.st_size > 500000:  # > 500KB (likely high-res photos)
                dat_files.append((stat.st_mtime, full, stat.st_size))

dat_files.sort(reverse=True)
print(f"Found {len(dat_files)} large .dat files (>500KB)")

from datetime import datetime

# Try to decode the most recent ones
for mtime, path, size in dat_files[:30]:
    with open(path, 'rb') as f:
        header = f.read(4)
    
    # WeChat XOR key: first byte XOR with JPEG (0xFF) or PNG (0x89)
    key = header[0] ^ 0xFF  # Assume JPEG
    
    # Verify: after XOR, should be FF D8 FF (JPEG magic)
    decoded = bytes([b ^ key for b in header])
    is_jpeg = decoded[:3] == b'\xff\xd8\xff'
    
    if is_jpeg:
        dt = datetime.fromtimestamp(mtime)
        print(f"  {os.path.basename(path)}: {size//1024}KB, {dt.strftime('%Y-%m-%d %H:%M')}, JPEG OK, key=0x{key:02X}")
    else:
        key_png = header[0] ^ 0x89
        decoded_png = bytes([b ^ key_png for b in header])
        if decoded_png[:4] == b'\x89PNG':
            dt = datetime.fromtimestamp(mtime)
            print(f"  {os.path.basename(path)}: {size//1024}KB, {dt.strftime('%Y-%m-%d %H:%M')}, PNG OK, key=0x{key_png:02X}")
        else:
            dt = datetime.fromtimestamp(mtime)
            print(f"  {os.path.basename(path)}: {size//1024}KB, {dt.strftime('%Y-%m-%d %H:%M')}, UNKNOWN (decoded: {decoded.hex()})")

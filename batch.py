import subprocess

for i in range(76, 87):  # 87 is exclusive, so up to 86
    subprocess.run(['py', 'video.py', str(i)])
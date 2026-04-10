import subprocess

out = subprocess.check_output(['docker', 'compose', 'logs', '--tail=500', 'backend'], text=True)
with open('err4.txt', 'w', encoding='utf-8') as f:
    f.write(out[-10000:])

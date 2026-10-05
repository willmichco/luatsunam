from pathlib import Path
import shutil, subprocess,sys
root=Path(__file__).resolve().parent.parent
subprocess.run([sys.executable,str(root/'tools/build.py')],check=True)
dist=root/'dist'
if dist.exists(): shutil.rmtree(dist)
dist.mkdir()
for f in root.iterdir():
 if f.name in {'dist','src','tools','.git','.github','.openai','.sites-runtime','README.md','README-DELIVERY.md','.gitignore'} or f.name.startswith('.'):continue
 if f.is_dir():shutil.copytree(f,dist/f.name,dirs_exist_ok=True)
 elif f.suffix in {'.html','.txt','.xml','.webmanifest'}:shutil.copy2(f,dist/f.name)
print('Static output:',dist)

"""Build a public-file allowlist for Vercel, without network access."""
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parent
PUBLIC_FILES = ('index.html', 'explorer.js', 'theme.css', 'sea-friends.svg', 'preview-data.js')

def build(output=None):
    output = Path(output) if output else ROOT / 'public'
    output.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_FILES:
        copyfile(ROOT / name, output / name)
    (output / 'assets').mkdir(exist_ok=True)
    for image in (ROOT / 'assets').glob('*.jpg'):
        copyfile(image, output / 'assets' / image.name)
    return output

if __name__ == '__main__':
    directory = build()
    print('Static website prepared in', directory.name + '/')

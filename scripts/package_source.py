"""Build a source-only archive without local credentials or business data."""

import fnmatch
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parent.parent
ALLOWED_DIRECTORIES = {'apps', 'common', 'config', 'scripts'}
ALLOWED_SUFFIXES = {'.py', '.sql', '.txt'}
ALLOWED_API_DOCS = {
    'docs/users-api.md', 'docs/organization-api.md', 'docs/datahub-api.md',
    'docs/performance-api.md', 'docs/workflow-api.md',
}
ALLOWED_ROOT_FILES = {
    'README.md', 'requirements.txt', '.env.example',
    '.gitignore', '.dockerignore', '.python-version', 'Dockerfile',
    'docker-compose.yml', 'manage.py', 'dbtool_service.py',
    'gunicorn_conf.py', 'start.sh', 'local.sh', 'request_test.py',
}
PRIVATE_PATTERNS = (
    '.env', '.env.*', 'config.json', 'config.*.json', '*.pem', '*.key',
    '*.p12', '*.pfx', '*.jks', 'id_rsa*', 'id_ed25519*', '*.bak',
)


def is_shareable(name):
    path = Path(name)
    if name == '.env.example':
        return True
    if any(part.startswith('.') or part in {'private', 'secrets', '__pycache__'}
           for part in path.parts):
        return name in ALLOWED_ROOT_FILES
    if any(fnmatch.fnmatch(path.name, pattern) for pattern in PRIVATE_PATTERNS):
        return False
    if name in {'config/settings/local.py', 'config/settings/private.py'}:
        return False
    return name in ALLOWED_ROOT_FILES or name in ALLOWED_API_DOCS or (
        path.parts[0] in ALLOWED_DIRECTORIES and path.suffix in ALLOWED_SUFFIXES
    )


def main():
    # Include current tracked and unignored new source files, not stale HEAD contents.
    result = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=ROOT, check=True, capture_output=True,
    )
    names = sorted(set(result.stdout.decode().rstrip('\0').split('\0')))
    target = ROOT / 'project.zip'
    temporary = ROOT / 'project.zip.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in names:
                source = ROOT / name
                if not name or not is_shareable(name) or not source.is_file():
                    continue
                if source.is_symlink():
                    continue
                if not source.resolve().is_relative_to(ROOT):
                    continue
                archive.write(source, name)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'Source archive created: {target.name}')
    print('Private files and datasets are excluded. Review source changes before sharing.')


if __name__ == '__main__':
    main()

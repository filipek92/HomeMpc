#!/usr/bin/env python3
import sys
import yaml
import json
import subprocess
from datetime import datetime

CONFIG_FILE = 'config.yaml'
CHANGELOG_FILE = 'CHANGELOG.md'
REPOSITORY_FILE = 'repository.json'

def get_current_version():
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    version = config.get('version', '0.0.0')
    return version

def bump_version(version, part):
    major, minor, patch = map(int, version.split('.'))
    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    elif part == 'patch':
        patch += 1
    else:
        raise ValueError('Invalid version part')
    return f"{major}.{minor}.{patch}"

def update_config_yaml(new_version):
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    config['version'] = new_version
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

def update_repository_json(new_version):
    with open(REPOSITORY_FILE) as f:
        repo_data = json.load(f)
    
    # Aktualizuj verzi v addon sekci
    for addon in repo_data.get('addons', []):
        if addon.get('slug') == 'power_stream_plan':
            addon['version'] = new_version
            break
    
    with open(REPOSITORY_FILE, 'w') as f:
        json.dump(repo_data, f, indent=2)

def get_last_tag():
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode().strip()
    except subprocess.CalledProcessError:
        tag = None
    return tag

# Function to get the last commit message if no message provided
def get_last_commit_message():
    try:
        msg = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%s']).decode().strip()
    except subprocess.CalledProcessError:
        msg = ''
    return msg

def get_commits_since(tag):
    if tag:
        rev_range = f'{tag}..HEAD'
    else:
        rev_range = 'HEAD'
    log = subprocess.check_output(['git', 'log', '--pretty=format:%s', rev_range]).decode().strip()
    return log.split('\n') if log else []

def update_changelog(new_version, message, commits):
    date = datetime.now().strftime('%Y-%m-%d')
    entry = f"\n## {new_version} - {date}\n{message}\n"
    if commits:
        entry += '\n'.join(f'- {c}' for c in commits)
        entry += '\n'
    with open(CHANGELOG_FILE, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(entry + '\n' + content)

def git_commit_and_tag(new_version):
    subprocess.check_call(['git', 'add', CONFIG_FILE, CHANGELOG_FILE, REPOSITORY_FILE])
    subprocess.check_call(['git', 'commit', '-m', f'Release version {new_version}'])
    subprocess.check_call(['git', 'tag', f'v{new_version}'])
    subprocess.check_call(['git', 'push'])
    subprocess.check_call(['git', 'push', '--tags'])

def main():
    if len(sys.argv) < 2:
        print('Použití: publish_version.py [major|minor|patch] ["zpráva"]')
        sys.exit(1)
    part = sys.argv[1]
    if len(sys.argv) >= 3:
        message = sys.argv[2]
    else:
        message = get_last_commit_message()
    old_version = get_current_version()
    new_version = bump_version(old_version, part)
    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)

    # Kontrola čistoty pracovního adresáře
    status = subprocess.check_output(['git', 'status', '--porcelain']).decode().strip()
    if status:
        print('Chyba: Pracovní adresář není čistý. Uložte nebo zahoďte změny před publikací verze.')
        sys.exit(1)

    print('--- Shrnutí publikace verze ---')
    print(f'Stará verze: {old_version}')
    print(f'Nová verze: {new_version}')
    print(f'Zpráva: {message}')
    print(f'Git tag: v{new_version}')
    print('Commity od poslední verze:')
    if commits:
        for c in commits:
            print(f'  - {c}')
    else:
        print('  (žádné commity)')
    confirm = input('Pokračovat? (y/n): ').strip().lower()
    if confirm != 'y':
        print('Publikace zrušena.')
        sys.exit(0)

    update_config_yaml(new_version)
    update_repository_json(new_version)
    update_changelog(new_version, message, commits)
    git_commit_and_tag(new_version)
    print(f'Verze {new_version} publikována.')

if __name__ == '__main__':
    main()

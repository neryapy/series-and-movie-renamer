import os
import re
import requests
OMDB_API_KEY = str(input("api key of ombd"))  # Replace with your OMDb API key
# --- Fetch metadata from OMDb ---
def fetch_metadata_from_omdb(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                actors = data.get("Actors", "Unknown").split(",")[:2]
                genre = data.get("Genre", "Unknown").split(",")[0]
                year = data.get("Year", "Unknown")
                runtime = data.get("Runtime", "Unknown")
                return {
                    "actors": " & ".join(actor.strip() for actor in actors),
                    "genre": genre.strip(),
                    "year": year.strip(),
                    "runtime": runtime.strip()
                }
    except Exception as e:
        print(f"Error fetching metadata for {title}: {e}")
    
    return {
        "actors": "",
        "genre": "",
        "year": "",
        "runtime": ""
    }

# --- Extract duration from file ---
def extract_duration_from_file(file_path):
    try:
        probe = ffmpeg.probe(file_path, v='error', select_streams='v:0', show_entries='stream=duration')
        duration = float(probe['streams'][0]['duration'])
        minutes = int(duration // 60)
        return f"{minutes} min"
    except Exception as e:
        print(f"Error extracting duration for {file_path}: {e}")
        return "Unknown"

# --- Sanitize filename ---
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

# --- Detect if folder is a movie folder ---
def is_movie_folder(name):
    return bool(re.search(r'\d{4}', name))  # e.g. contains a year
def clean_filename(filename, directory, is_folder=False, video_path=None):
    name, ext = os.path.splitext(filename)

    technical_tags = ['1080p', '720p', 'X264', 'X265', 'H264', 'H265', 'AVC', 'DTS', 'DDP',
                      'HDR', 'DV', 'AAC', 'AC3', 'WEB', 'WEB-DL', 'BluRay', 'NF', 'FTMVHD','WEB-DL','FTMVHD','[',']','fr','en','(',')',
                      'Max2Power', 'Vfq', 'Voa', 'VFQ', 'VFF', 'BTT', 'MULTI', 'AV1', 'EAC3','-']
    language_tags = ['FRENCH', 'TRUEFRENCH', 'ENGLISH', 'GERMAN', 'SPANISH']

    clean_tags = set(tag.upper() for tag in technical_tags + language_tags)

    file_path = video_path if is_folder else os.path.join(directory, filename)

    # TV Show match
    match = re.match(r'^(.*?)[. _-](S\d{2}E\d{2})[. _-](.*)$', name, re.IGNORECASE)

    if match:
        show_raw, season_episode, rest = match.groups()
        parts = re.split(r'[.\s_\-]+', rest)
        title_parts = [p for p in parts if p.upper() not in clean_tags]

        show_title = re.sub(r'[._-]', ' ', show_raw).strip().title()
        episode_title = ' '.join(title_parts).strip().title()

        # Final clean name
        new_name = f"{show_title} - {season_episode.upper()}"
        if episode_title:
            new_name += f" - {episode_title}"
        if not is_folder:
            new_name += ext
    else:
        # Movie match
        parts = re.split(r'[.\s_\-]+', name)
        title_parts = []
        for part in parts:
            if part.upper() in clean_tags or re.search(r'\d{3,4}p', part, re.IGNORECASE):
                break
            title_parts.append(part)

        movie_title = ' '.join(title_parts).strip().title()
        new_name = movie_title
        if not is_folder:
            new_name += ext

    return sanitize_filename(new_name)
def rename_files_in_directory(root_directory):
    for current_dir, subdirs, files in os.walk(root_directory, topdown=False):
        # Rename video files
        for filename in files:
            if filename.lower().endswith(('.mp4', '.mkv', '.avi')):
                full_path = os.path.join(current_dir, filename)
                try:
                    new_name = clean_filename(filename, current_dir)
                    dst = os.path.join(current_dir, new_name)
                    if new_name != filename:
                        print(f"Renaming file:\n  {filename}\n-> {new_name}\n")
                        os.rename(full_path, dst)
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

        # Rename movie folders
        for folder in subdirs:
            folder_path = os.path.join(current_dir, folder)
            if is_movie_folder(folder):
                try:
                    video_file = next(
                        (f for f in os.listdir(folder_path) if f.lower().endswith(('.mp4', '.mkv', '.avi'))),
                        None
                    )
                    if video_file:
                        video_path = os.path.join(folder_path, video_file)
                        new_name = clean_filename(folder, current_dir, is_folder=True, video_path=video_path)
                        dst = os.path.join(current_dir, new_name)
                        if new_name != folder:
                            print(f"Renaming folder:\n  {folder}\n-> {new_name}\n")
                            os.rename(folder_path, dst)
                except Exception as e:
                    print(f"Error processing folder {folder}: {e}")

# --- Main ---
if __name__ == "__main__":
    folder_path = input("Enter path:\n").strip()
    if not os.path.isdir(folder_path):
        print("❌ Invalid path.")
    else:
        rename_files_in_directory(folder_path)

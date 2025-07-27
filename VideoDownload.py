import re
import os
import time
import glob
import logging
from dataclasses import dataclass
from typing import Any
from logging.handlers import RotatingFileHandler

LOGGER_NAME = 'videodownloadapp'
LOG_MAXSIZE = 4 * 1024 * 1024 # 4MB
LOG_BACKUPCOUNT = 5
LOGFILE = 'videodownloadapp.log'
LOG_LEVEL = logging.INFO

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LOG_LEVEL)
logger.propagate = False
logger.handlers.clear()
handler = RotatingFileHandler(
    LOGFILE,
    maxBytes=LOG_MAXSIZE,
    backupCount=LOG_BACKUPCOUNT
)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
handler.setLevel(LOG_LEVEL)
logger.addHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

try:
    from pydantic import BaseModel
    from tqdm import tqdm
    import yt_dlp
    from yt_dlp.utils import DownloadError,YoutubeDLError
    import ffmpeg
    from youtubesearchpython import VideosSearch
    import configparser
    from configparser import ConfigParser
except ImportError as e:
    logger.error(f"{e.name} is not installed. Please install the required dependencies.")
    exit(1)

# ! Remember to use ENV or you will not have the correct HTTP and get proxy errors
# source .venv/bin/activate

class VideoResult(BaseModel):
    """ Model for single video. """
    id: str
    title: str
    link: str
    duration: str
    channel: dict[str,Any]

class VideosSearchResult(BaseModel):
    """ Model for search result response. """
    result: list[VideoResult]

class SongErrors:
    """ Static Song error container. """
    errored_yttitles: list[str | None] = []  
    errored_songfile: list[str] = [] 

    @staticmethod
    def add_song(vid_title: str|None, filename: str) -> None:
        SongErrors.errored_yttitles.append(vid_title)
        SongErrors.errored_songfile.append(filename)

    @staticmethod
    def get_all_errors() -> dict[str,list[Any]]:
        return {
            "errored_yttitles": SongErrors.errored_yttitles,
            "errored_songfile": SongErrors.errored_songfile
        }

    @staticmethod
    def clear_errors() -> None:
        SongErrors.errored_yttitles.clear()
        SongErrors.errored_songfile.clear()

class ProgressRef:
    """ Reference for Progress bar / Processing count """
    def __init__(self, bar:tqdm, count:int=0):
        self.count:int = count
        self.bar:tqdm = bar

def clean_cookie() -> None:
    """ Cleanup any google-cookies sticking around. """
    if os.path.exists(".google-cookie"):
        os.remove(".google-cookie")

def convert_to_webm(output_folder: str) -> None:
    """ Convert video file from source type to WebM. """
    input_path = os.path.join(output_folder, 'video.mp4')
    output_path = os.path.join(output_folder, 'output.webm')
    final_path = os.path.join(output_folder, 'video.webm')
    logger.info('Formatting downloaded video for Clone Hero in WebM format...')
    try:
        if not os.path.exists(input_path):
            logger.error(f"Input MP4 file not found at {input_path}. Skipping conversion.")
            return
        ffmpeg.input(input_path).output(
                output_path, 
                vcodec='libvpx',
                crf=10, # Constant Rate Factor: controls quality (lower is higher quality)
                bandwidth='8M', # Bitrate: target bitrate; here, 8 Megabits per second
                acodec='libvorbis' # Audio codec: Vorbis (WebM compatible audio codec clonehero requires)
            ).run(overwrite_output=True, quiet=True)
        if os.path.exists(output_path):
            os.rename(output_path, final_path)
            logger.info("SUCCESS: Conversion succeeded!")            
            remove_existing_video(input_path)           
        else:
            logger.error("Conversion failed output.webm not found.")        
    except Exception as e:
        logger.error(f'Error while converting video, {str(e)}')

def download_video(ydl: yt_dlp.YoutubeDL, url: str, video_quality: str, target_folder: str) -> bool:
    """ Facilitate actual download. """
    try:
        url_list:list[str]=[url]
        _ = ydl.download(url_list)
        if video_quality != 'webm':
            convert_to_webm(target_folder)
        else:
            logger.info('SUCCESS: Video already in WebM format!')
        return True
    except DownloadError as e:
        logger.error(f"Download error from {url}: {str(e)}")
        return False
    except YoutubeDLError as e:
        logger.error(f"yt-dlp error from {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error {str(e)}")
        return False

def try_download_videos(ydl: yt_dlp.YoutubeDL, urls: list[str | None], video_quality: str,target_folder:str) -> bool:
    """ Attempt download per URL. """
    for url in filter(None, urls):
        if download_video(ydl, url, video_quality,target_folder):
            logger.info(f"SUCCESS: Downloaded from {url}.")
            return True
        else:
            logger.warning(f"Failed to download from {url}. Trying next...")
    logger.error(f"Failed to download from all provided URLs.")
    return False

def get_video_urls(song_search_term:str)-> tuple[str | None, str | None, str | None]:
    """ Gets video URLs based on search term."""
    # Some song names have strings that will cause YouTube to search for a Clone Hero/Rock Band playthrough video. This strips that out
    song_search_term = re.sub(r'\(.*?\)', '', song_search_term).strip()  # Regex to remove parens and contents
    title_filter: list[str] = [
        '(2x Bass Pedal Expert+)', 
        '(2x Bass Pedal)', 
        'RB3', 
        '(RB3 version)', 
        '(Rh)',
        'Harmonix',            
        'Rock Band',        
        'Clone Hero',       
        'Expert+',          
        'Expert',           
        'Hard',             
        'Pro Guitar',       
        'Pro Drums',        
        'Guitar Hero',      
        'Rocksmith',        
        'Playthrough',      
        'Gameplay',         
        'Rhythm Game',      
        'Expert Mode',      
        'Instrumental',     
        'No Fail',          
        'Full Combo',       
        'SFX',              
        'Tutorial',         
        'FC',               
        'Score',            
        'Band',             
        'Drum Cover',       
        'Guitar Cover',     
        'CloneHero',        
        'GuitarHeroLive',   
        'Clone Hero Custom', 
        'Clone Hero Playlist', 
        'Custom Song',      
        'Track Pack',       
        'Drum Hero',        
        'Rock Band 4',      
        'Rock Band 3',      
        'Rock Band Rivals', 
        'Guitar Hero World Tour', 
        'Guitar Hero Live', 
        'Clone Hero Setup', 
        'Rhythm Game Cover',   
        'Hero',
        'Trailer'
    ]
    # This only filters the current song folder names NOT the query results
    for invalid in title_filter:
        song_search_term = song_search_term.replace(invalid, '')
    query: str = f'{song_search_term} (Official Music Video)'
    logger.info("\n")
    logger.info(f'Looking on YouTube for: {query}')
    # finds the top 2 video URLs from YouTube
    try:
        youtube_result:str | dict[str,Any] = VideosSearch(query, limit=2).result()
        if not isinstance(youtube_result, dict):
            logger.error(f"Unexpected result type: {type(youtube_result)}")
            return None, None, None        
        validated = VideosSearchResult(result=youtube_result.get("result", []))
        if not validated.result:
            logger.warning(f"No videos found for {song_search_term}.")
            return None, None, None
        result_list = validated.result
        url, url2, video_title = None, None, None
        if len(result_list) == 1:
            url = result_list[0].link
            video_title = result_list[0].title
            url2 = url  # Fallback to the same URL if no second video is found 
            logger.warning(f"Only found one video for {song_search_term}. Attempting to download from the single URL.")
        elif len(result_list) >= 2:
            url = result_list[0].link
            video_title = result_list[0].title
            url2 = result_list[1].link
            logger.info(f"Found at least two videos for {song_search_term}. Attempting download.")
        logger.info(f"SUCCESS: Downloading from {video_title} - URL 1: {url}, URL 2: {url2}")
    except Exception as e:
        logger.error(f"Error searching YouTube for {song_search_term}: {str(e)}")
        return None, None, None  # Return None if there's an error
    return url, url2, video_title

def update_song_ini(song_ini_path,filename) -> tuple[bool|None,str|None]:
    """ Update song.ini to attempt to sync video. """
    config: ConfigParser = configparser.ConfigParser()
    try:
        if not os.path.exists(song_ini_path):  # Check if the file exists
            logger.error("No 'song.ini' found. Skipping.")
            return (False,filename)
        with open(song_ini_path, 'r') as song_ini:
            content = song_ini.read()
            # check if the ini file contains unexpected phase shift converter text
            if '//Converted' in content:
                logger.error(f"Problem syncing video for {filename}. Added to error list.")
                return (False,filename)
            config.read_string(content)
        # Check if the necessary sections exists
        if config.has_section('song'):
            config.set('song', 'video_start_time', '-3000')
        elif config.has_section('Song'):
            config.set('Song', 'video_start_time', '-3000')
        else:
            logger.error(f"Missing 'song' or 'Song' section in song.ini for {filename}.")     
            return (False,filename)             
        # Write changes back to the file
        with open(song_ini_path, 'w') as config_file:
            config.write(config_file)
        logger.info('SUCCESS: Song ready. Next song...\n')
    except Exception as e:
        logger.error(f"Error updating song.ini for {filename}: {str(e)}")
        return (False,filename)
    return (True,None)

@dataclass
class UserSelectOption:
    option_text:str
    option_notice:str
    option_result:str
    option_overwrite: bool

def get_quality_input()-> tuple[str, bool]:
    """Gets the quality requested via user input."""
    quality_data:list[UserSelectOption]=[
        UserSelectOption("Default quality (720p)","Set to 720p .","mp4",False),
        UserSelectOption("Best quality where available (1080p bigger files)","Set to 1080p. Poor hard drive!","bestvideo[vcodec^=avc]/best[ext=mp4]/best",False),
        UserSelectOption("[EXPERIMENTAL] Replace existing videos with 1080p (Caution: Use at your own risk. May malfunction and remove videos)","Replacing all videos with 1080p. You have time for a nap!","bestvideo[vcodec^=avc]/best[ext=mp4]/best",True),        
    ]
    input_prompt = f"Type the number to pick from the following options:\n"
    for index, item in enumerate(quality_data):
        input_prompt += f"{index+1}. {item.option_text}\n"
    input_prompt += f"Pick between 1-{len(quality_data)}: "
    while True:
        quality_input: str = input(input_prompt)
        try:
            selected_option = int(quality_input)
            if 1 <= selected_option <= len(quality_data):
                item = quality_data[selected_option - 1]
                logger.info(f"Result: {item.option_notice}")
                return item.option_result, item.option_overwrite
            else:
                logger.error(f'You must choose between 1-{len(quality_data)}. Try again!')
        except ValueError:
            logger.error(f"You must choose a valid number between 1-{len(quality_data)}. Try again!")

def get_songs_folder()->str|None:
    """Validates Songs folder and returns it."""
    found_songs_folder:bool = False
    s_folder:str | None = None
    for root, _dirs, _files in os.walk(os.getcwd()):
        if os.path.basename(root).lower() == 'songs':
            s_folder = root
            found_songs_folder = True
            break
    if not found_songs_folder:
        emsg="No 'Songs' folder found. Please ensure it's in the correct location."
        logger.error(emsg)
        return None
    return s_folder

def prompt_user_to_exit() -> None:
    """Does what it says."""
    _ = input(f"Press Enter button to exit.")

def get_total_song_count(folder:str) -> int:
    """Returns Song count."""
    song_files: list[str] = glob.glob(os.path.join(folder, "**", "song.ini"), recursive=True)
    return len(song_files)

def remove_existing_video(file_path: str) -> None:
    """Removes video at filepath if matches extensions."""
    allowed_extensions = {".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm"}
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in allowed_extensions:
        logger.error(f"'{ext}' is not a valid removal extension.")
        return

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"SUCCESS: Removed {filename} from {directory}.")
        else:
            logger.warning(f"{filename} not found in {directory} for removal.")
    except OSError as e:
        logger.error(f"Cannot remove {filename} in {directory}: {e}")

def new_ydl_options(outfile:str,format:str,overwrites:int,playlist:int,quiet:bool):
    """Produces a YDL options dict."""
    return {
                'outtmpl': outfile,
                'format': format,
                'nooverwrites': overwrites,
                'noplaylist': playlist,
                'quiet': quiet
            }

def report_song_errors() -> None:
    """Logs Song errors at end of processing."""
    errors = SongErrors.get_all_errors()
    if errors['errored_yttitles'] or errors['errored_songfile']:
        logger.error("The following videos were downloaded but not audio-synced:")
        for title in errors['errored_yttitles']:
            logger.error(f"{title}")
        for filename in errors['errored_songfile']:
            logger.error(f"{filename}")
    else:
        logger.info("\n")
        logger.info("No song processing errors reported.")

def update_processed(progress_ref:ProgressRef) -> None:
    """Updates progress references."""    
    progress_ref.count+=1   
    _ = progress_ref.bar.update() 

def initialize_progress(total: int) -> ProgressRef:
    """Creates progress references."""
    progress_bar = tqdm(total=total, unit=" videos")
    return ProgressRef(progress_bar)

def should_process_song(song_folder: str, current_song_name: str, replace_song: bool) -> bool:
    """Determines if a song should be processed based on existing video and replace preference."""
    logger.info(f"Checking processing on {current_song_name}...")

    final_video_path = os.path.join(song_folder, "video.webm")
    vid_path_no_exist = not os.path.exists(final_video_path)
    cur_song_not_errored = current_song_name not in SongErrors.errored_songfile
    should_process = (vid_path_no_exist and cur_song_not_errored) or replace_song
    
    logger.debug(f"Allowed to process? {should_process}")
    
    return should_process

def download_then_convert_song(
    song_folder: str,
    current_song_name: str,
    video_quality: str
) -> tuple[str | None, bool]:
    """Handles the downloading and conversion steps for a single song."""
    video_title: str | None = None
    try:
        # Cleanup previous videos in the specific song folder
        remove_existing_video(os.path.join(song_folder, 'video.mp4'))
        remove_existing_video(os.path.join(song_folder, 'video.webm'))
        
        url, url2, video_title = get_video_urls(current_song_name)
        if not url and not url2:
            logger.warning(f"No valid video URLs found for {current_song_name}. Cannot download.")
            return video_title, False # Indicate failure due to no URLs

        output_mp4_path = os.path.join(song_folder, 'video.mp4')
        ydl_opts = new_ydl_options(output_mp4_path, video_quality, 0, 1, True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if not try_download_videos(ydl, [url, url2], video_quality, song_folder):
                logger.error(f"Failed to download video from YouTube for {current_song_name}.")
                return video_title, False # Indicate download failure

        return video_title, True # Indicate success
    except Exception as e:
        logger.error(f"An unexpected error occurred during download/conversion for {current_song_name}: {e}")
        return video_title, False # Indicate failure

def process_single_song(filename: str, progress_ref: ProgressRef, video_quality: str, replace_song: bool) -> None:
    """Processes a single song, including video download and song.ini update."""
    song_folder = os.path.dirname(filename)
    current_song_name = os.path.basename(song_folder)
    video_title: str | None = None

    if not should_process_song(song_folder, current_song_name, replace_song):
        logger.warning(f"Skipping {current_song_name}: video exists or previously errored, and replace not selected.")
        update_processed(progress_ref)
        return

    logger.info(f"Prepping for video download and processing for {current_song_name}...")
    
    video_title, download_success = download_then_convert_song(song_folder, current_song_name, video_quality)
    
    if not download_success:
        SongErrors.add_song(video_title, current_song_name)
        update_processed(progress_ref)
        return # Skip to next song if download/conversion failed

    _ini_success, update_song_ini_error_filename = update_song_ini(os.path.join(song_folder, 'song.ini'), current_song_name)
    
    if update_song_ini_error_filename: # If there was an error updating ini
        SongErrors.add_song(video_title, update_song_ini_error_filename)
        update_processed(progress_ref)
        return # Skip to next song

    clean_cookie()
    update_processed(progress_ref)

def process_songs(songs_folder: str, video_quality: str, replace_song: bool) -> None:
    """ Processes all songs in songs_folder. """
    songs_generator = glob.iglob(os.path.join(songs_folder, "**", "song.ini"), recursive=True)
    total_count = get_total_song_count(songs_folder)
    progress_ref = initialize_progress(total_count)
    logger.info(f"Total songs to process: {total_count} ...")

    for filename in songs_generator:
        process_single_song(filename, progress_ref, video_quality, replace_song)

    report_song_errors()
    logger.info(f"All downloads complete. Checked a total of {total_count} songs. ")
    prompt_user_to_exit()

def main() -> None:
    clean_cookie()
    logger.info('Checking for Songs folder...')
    target_songs_folder = get_songs_folder()
    if target_songs_folder:
        logger.info('SUCCESS: Songs folder found!\n')   
        time.sleep(0.5)
        video_quality, replace_song = get_quality_input()
        process_songs(target_songs_folder, video_quality, replace_song)
    else:
        logger.error("Did not detect a 'Songs' folder. Check you have placed the script in the directory one level above it.")
        prompt_user_to_exit()

if __name__ == '__main__':
    main()
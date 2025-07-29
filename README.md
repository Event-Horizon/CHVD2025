<img src="https://github.com/Event-Horizon/CHVD2025/raw/master/assets/icon.png" width="32" height="32"></img> 

# CHVD 2025

> A refactor of CloneHeroVideoDownloader: 
> 
> a simple application that allows you to automatically download the top YouTube video result for songs in your Clone Hero library.

### Disclaimer

This software is provided "as-is," without any warranties or guarantees of any kind. The author shall not be held responsible or liable for any damages, losses, or issues arising from the use or inability to use this software, including but not limited to data loss, system crashes, or any other consequences. Use this software at your own risk.

### App Description
Clone Hero recognises `video.mp4` file in every song folder as the video to play in the background of the song chart. 

1. This program recursively runs through your Clone Hero songs folder to find songs that are missing this `video.mp4` file. 

2. You are given three options for quality:
    - 720p (average 5-50MB per video)
    - 1080p (100MB+ per video)
    - Replace 1080p (100MB+ per video AND deletes every video file you already have and replaces it with 1080p)
  
> Note: Options lower than 720p are not included as the quality is so degraded at that stage that it is not really worth even having.

3. If the file is missing, it then searches YouTube and grabs the first result for that song, using the folder name as the search string. 
4. If the download of the first search result fails, it attempts to download the second top result. 
5. Once downloaded, the file is renamed to 'video.mp4' and placed in the song folder. 
6. After this, Clone Hero should automatically recognise the video file and play it during the song.
7. As YouTube by default does not provide h264 encoded videos above 720p, ffmpeg is used to remux 1080p videos into a format Clone Hero can play (WebM so it also works on Linux).
8. Then it moves on to next song

A progress bar is provided to indicate how many videos still need to be downloaded and will attempt to estimate the time remaining.

This program has also been designed to run multiple times on the same songs directory. If you add new songs to Clone Hero, simply re-run the program and it will only download the videos that are missing. Should any songs run into errors, this will be displayed once the program has finished running.

### Usage

## Run with BASH:

```bash 
bash run_videodownload.sh
```

## Run with POWERSHELL:

```powershell 
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

.\run_videodownload.ps1
```

## Run as PYTHON script:
1. Clone this repository into your Clone Hero directory, one level above your Songs folder:
    ```bash
    /home/Event-Horizon/.clonehero/VideoDownload.py
    ```
2. Open Terminal/CMD/Powershell
3. Create the .venv: `python3 -m venv .venv` or `python -m venv .venv`
4. Make sure you activate the venv: 
    - Linux: `source .venv/bin/activate`
    - Windows: `.venv/bin/activate.bat` or `.venv/bin/Activate.ps1`
5. Install required dependencies from requirements.txt: ```python install -r requirements.txt```
6. Run VideoDownload.py ```python VideoDownload.py```

### Notes/FAQ

**WARNING**: If you are not in the `.venv` when installing requirements you may accidently install the requirements globally!

If you receive a `proxy/proxies` error, this means you did not run the app from the `.venv` after installing requirements in it OR it means requirements were not installed.

If you are worried about editing Songs in place, copy Songs into the cloned folder of this project instead of cloning to the Clone Hero folder. Then when you are done DLing videos copy back and delete the extra left behind Songs folder.

Conversion info is dependent on what Clone Hero allows in their code for videos, if it changes this must get updated.

Updated with some scripts to make running this a little less painful for users. - Event-Horizon 7/28/25

### Credits

> Original Creators: [jshackles](https://github.com/jshackles) , [stripedew](https://github.com/stripedew/) , [nreichen](https://github.com/nreichen)

> Refactored Code: [Event-Horizon](https://github.com/Event-Horizon)

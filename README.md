# CaptionForge

## Overview
The CaptionForge is a desktop application built with PyQt5, designed to allow users to play videos, generate subtitles automatically, edit them, and export the changes. It supports various video and audio formats, providing an integrated environment for video playback and subtitle editing. 

## Features
- Video playback with customizable controls
- Automatic transcription and subtitle generation for video and audio files
- Batch processing for transcribing multiple files
- Subtitle editing in a dedicated text box
- Exporting video with edited subtitles 
- Search functionality within subtitles
- Volume control and playback information display

## Installation 

### Prerequisites
- Python 3.6 or higher
- PyQt5 
- ffmpeg (for video and audio processing)
- whisper (for transcription)

### Steps

1. Ensure Python and pip are installed on your system.
2. Install PyQt5 using pip: 
`pip install PyQt5`
3. Install ffmpeg and whisper following their respective installation guides. 
- ffmpeg: [FFmpeg Installation guide](https://ffmpeg.org/download.html)
- whisper: Instructions can be found in its GitHub repository or documentation.

### Using a Conda Environment

To simplify the setup process, I recommend using a Conda environment. This approach ensures that all dependencies are installed and contained, avoiding conflicts with other packages on your system. 

1. **Install Anaconda or Miniconda**
- If you havent already, download and install Anaconda or Miniconda from their [own personal site](https://docs.anaconda.com/free/anaconda/install/).
2. **Create the Environment** 
- Download the **whisper.yml** file from the repository.
- Open a terminal or command prompt.
- Navigate to the directory containing the **whisper.yml** file.
- Create the Conda environment by running: 
`conda env create -f whisper.yml`
- This command reads the **whisper.yml** file and sets up an environment named **whisper** with all required dependencies. 
3. **Activate the Environment**
- Once the environment is successfully created, activate it with:
    `conda activate whisper`
- Ensure that you activate this environment each time you work with the application to use the correct dependencies.
### Running the Application
With the environment activated, navigate to the application's directory in your terminal or command prompt and run: 
  `python transcribe.py`

### Usage 

**Open a Video**: Use the "Open Video" option in the combo box to select and play a video file. Upon selection, the video will play in the integrated video player.
**Generate Subtitles**: Select "Transcribe File" to automatically generate subtitles for the current video. The program processes the video and audio content to create a subtitles file. During this process, a subdirectory named '**processedFiles**' is created in the same directory as your source video file. All processed files, including the generated '**.mp4**' and corresponding '**.srt**' subtitle file, are saved in this subdirectory.
**Edit Subtitles**: To ensure accuracy and customization, you can edit the automatically generated subtitles. Click on "Toggle Edit Mode" to enable subtitle editing within the program. Make your changes and then click again to disable editing mode. **It is recommended to use the '.mp4' video file generated by the program for subtitle editing to ensure synchronization between the video content and the subtitles**. This guarantees that the edits you make correspond accurately to the video playback.
**Export Changes**: After editing, click on "Export Changes" to save your edited subtitles and apply them back to the video. The program updates the '**.srt**' subtitle file in the '**processedFiles**' subdirectory. For continuity and to avoid confusion, it's advised to work with the '**.mp4**' and '**.srt**' files located in the '**processedFiles**' subdirectory throughout the editing and exporting process.

**Batch Transcription**: For handling multiple files at once, choose "Batch Transcribe Files" to select a directory. The program will transcribe all suitable video and audio files within the selected directory, creating individual '**processedFiles**' subdirectories for each one. This feature streamlines the process of generating subtitles for numerous files, saving time and effort.

### Note
When working with subtitles in the '**processedFiles**' subdirectory, it's essential to maintain the pairing between the '**.mp4**' video files and their corresponding '**.srt**' subtitle files. This ensures that any edits or exports you perform use the correct subtitle file, maintaining accuracy in timing and content synchronization.

By following these usage guidelines, users can effectively generate, edit, and export subtitles, ensuring high-quality results with correct synchronization between the subtitles and video content.

### Troubleshooting

- **ffmpeg or whisper not found**: Ensure both tools are correctly installed and accessible in your system's PATH.
- **Video not playing**: Verify that the video format is supported and codecs are installed.

### Contributing

I welcome contributions and suggestions! Please open an issue or pull request on the GitHub repository.

### License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

The GNU Affero General Public License is a free, copyleft license for software and other kinds of works, specifically designed to ensure cooperation with the community in the case of network server software. For more information, visit the [GNU website](https://www.gnu.org/licenses/ag)

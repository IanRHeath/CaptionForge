import sys
import os
import subprocess
import shutil
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QProgressBar, QSlider, QTextEdit, QSizePolicy, QComboBox, QInputDialog, QDialog, QGridLayout, QStyle
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QPixmap

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        #Set window properties
        self.setWindowTitle("Subtitle Generator & Editor")
        self.setGeometry(100, 100, 800, 600)

        #Media player setup
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = QVideoWidget()
        self.videoWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        #Video controls setup
        self.videoScrubber = QSlider(Qt.Horizontal)
        self.videoScrubber.setRange(0, 0)
        self.currentTimeLabel = QLabel("Current Time: 00:00:00")

        #Subtitle related variables
        self.srt_filename = None
        self.subtitles = []

        #Combo box for different actions
        self.comboBox = QComboBox()
        self.comboBox.addItem("File")
        self.comboBox.addItem("Open Video")
        self.comboBox.addItem("Transcribe File")
        self.comboBox.addItem("Batch Transcrible Files")
        self.comboBox.addItem("Search Word")
        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)

        #Transcription progress widgets
        self.transcribeLabel = QLabel("Transcription Progress")
        self.label = QLabel('Status: Waiting for action...')
        self.progress = QProgressBar()

        #Playback control buttons
        self.playButton = QPushButton()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # Set play icon
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play_video)
        self.playButton.setFixedSize(64, 64)

        self.startOverButton = QPushButton()
        self.startOverButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.startOverButton.setEnabled(False)
        self.startOverButton.clicked.connect(self.start_over)
        self.startOverButton.setFixedSize(64, 64)

        self.rewindButton = QPushButton()
        self.rewindButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.rewindButton.setEnabled(False)
        self.rewindButton.clicked.connect(self.rewind_video)
        self.rewindButton.setFixedSize(64, 64)

        self.fastForwardButton = QPushButton()
        self.fastForwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.fastForwardButton.setEnabled(False)
        self.fastForwardButton.clicked.connect(self.fast_forward_video)
        self.fastForwardButton.setFixedSize(64, 64)

        #Toggle Edit Mode button
        self.toggleEditModeButton = QPushButton('Toggle Edit Mode', self)
        self.toggleEditModeButton.setCheckable(True)  # Makes the button toggleable
        self.toggleEditModeButton.clicked.connect(self.toggleEditMode)
        self.editMode = False
        self.currentlyEditingIndex = None
        self.userIsEditing = False

        #Layout setup
        controlButtonLayout = QHBoxLayout()
        controlButtonLayout.addWidget(self.rewindButton)
        controlButtonLayout.addWidget(self.playButton)
        controlButtonLayout.addWidget(self.fastForwardButton)

        mainButtonLayout = QVBoxLayout()
        mainButtonLayout.addLayout(controlButtonLayout)

        startOverButtonWrapper = QWidget()
        startOverButtonLayout = QHBoxLayout()  
        startOverButtonLayout.addWidget(self.startOverButton, 0, Qt.AlignCenter)  
        startOverButtonWrapper.setLayout(startOverButtonLayout)
       
        mainButtonLayout.addWidget(startOverButtonWrapper, 0, Qt.AlignCenter)

        self.exportChangesButton = QPushButton('Export Changes')
        self.exportChangesButton.setEnabled(False)  
        self.exportChangesButton.clicked.connect(self.export_changes)

        #Volume Control
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(100)
        self.volumeSlider.setToolTip('Volume')
        self.volumeSlider.valueChanged.connect(self.mediaPlayer.setVolume)

        #Textbox for displaying playback information
        self.textBox = QTextEdit()
        self.textBox.setReadOnly(True)
        self.textBox.setPlaceholderText("Playback Information...")
        self.textBox.setMaximumHeight(100)
        self.textBox.textChanged.connect(self.onTextBoxEdit)

        #Current time label
        self.currentTimeLabel = QLabel()

        #Button layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.rewindButton)
        buttonLayout.addWidget(self.playButton)
        buttonLayout.addWidget(self.fastForwardButton)

        #Time layout
        timeLayout = QHBoxLayout()
        timeLayout.addWidget(self.currentTimeLabel)
        timeLayout.addWidget(self.videoScrubber)

        #Final layout
        layout = QVBoxLayout()
        layout.addWidget(self.comboBox)
        layout.addWidget(self.videoWidget)
        layout.addLayout(mainButtonLayout)
        layout.addLayout(timeLayout)
        layout.addWidget(self.volumeSlider)
        layout.addWidget(self.toggleEditModeButton)
        layout.addWidget(self.textBox)
        layout.addWidget(self.exportChangesButton, 1)
        layout.addWidget(self.transcribeLabel)
        layout.addWidget(self.progress)
        layout.addWidget(self.label)
        layout.addWidget(self.currentTimeLabel)
        layout.addWidget(self.videoScrubber)

        #Set layout
        self.setLayout(layout)

        #Connecting signals and slots
        self.mediaPlayer.stateChanged.connect(self.media_state_changed)
        self.timer = QTimer(self)  
        self.timer.setInterval(100)  
        self.timer.timeout.connect(self.update_subtitles)  
        self.mediaPlayer.positionChanged.connect(self.update_current_time_label)
        self.videoScrubber.sliderMoved.connect(self.seek_video)
        self.mediaPlayer.durationChanged.connect(self.update_video_duration)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_temporary_changes)
        self.autosave_timer.start(180000)  # 180,000 milliseconds = 3 minutes

    '''Utility Methods'''

    def format_time(self, milliseconds):
        # Convert milliseconds to hours, minutes, seconds, and milliseconds
        hours = int(milliseconds // 3600000)  
        minutes = int((milliseconds % 3600000) // 60000)  
        seconds = int((milliseconds % 60000) // 1000)
        milliseconds = int(milliseconds % 1000)
        # Format the time into a string format HH:MM:SS,mmm
        formatted_time = f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
        return formatted_time

    def milliseconds_to_timestamp(self, ms):
        # Convert milliseconds to hours, minutes, seconds, and milliseconds
        hours = ms // (1000 * 60 * 60)
        minutes = (ms // (1000 * 60)) % 60
        seconds = (ms // 1000) % 60
        milliseconds = ms % 1000
        # Return the time in formatted string HH:MM:SS,mmm
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"  

    def time_to_milliseconds(self, time_str):
        # Split the input time string by ":" to get hours, minutes, and seconds
        splittime = time_str.split(":")
        # Convert hours, minutes, and seconds to milliseconds
        hours = float(splittime[0]) * 1000 * 60 * 60
        minutes = float(splittime[1]) * 1000 * 60
        milli = float(splittime[2].split(",")[0]) * 1000
        # Return the total milliseconds as an integer
        return int(hours + minutes + milli)

    def check_and_confirm_overwrite(self, file_path):
        # Check if the file exists at the given path
        if os.path.exists(file_path):
            # Prompt the user to confirm overwrite if the file exists
            reply = QMessageBox.question(self, 'File exists', "The file already exists. Do you want to overwrite it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            return reply == QMessageBox.Yes
        # Return True if the file does not exist
        return True
   
    def ensure_processed_files_dir_exists(self, file_path):
        # Extract the directory path from the file path
        file_dir = os.path.dirname(file_path)
        # Append directory name for processed files to the file directory
        processed_dir_path = os.path.join(file_dir, self.processed_files_dir)
        # Create the processed files directory if it doesn't already exist
        if not os.path.exists(processed_dir_path):
            os.makedirs(processed_dir_path)
        # Return the path to the processed files directory
        return processed_dir_path

    '''File Handling and Dialogue'''

    def open_file(self):
        # Open a file dialog to select a video file, with specified formats.
        self.filename, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        # Setup media player with the selected file and enable playback controls.
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))
        self.playButton.setEnabled(True)
        self.startOverButton.setEnabled(True)
        self.rewindButton.setEnabled(True)
        self.fastForwardButton.setEnabled(True)
        self.srt_filename = self.filename.split('.')[0] + ".srt"  # Assume subtitle file name.
        try:
            self.subtitles = self.parse_subtitles(self.srt_filename)  # Try loading subtitles.
        except FileNotFoundError:
            QMessageBox.warning(self, "Subtitle File Not Found", f"No SRT file found for {self.filename}.")
        self.timer.start()  # Start a timer for tracking playback and subtitle sync.

    def openFileNameDialog(self):
        # Open a file selection dialog with filtering options for transcription.
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select File for Transcription", "", "All Files (*);;MP3 Files (*.mp3);;MP4 Files (*.mp4);;WAV Files (*.wav);;MOV Files (*.mov)", options=options)
        if fileName:  # If a file was selected, proceed.
            self.convert_and_transcribe(fileName)  # Convert and transcribe the selected file.
            # Update the UI with the status of the transcription process.
            currentText = self.label.text()
            newMessage = f"Processing Complete for: {fileName}"
            self.label.setText(currentText + "\n" + newMessage if currentText else newMessage)

    def convert_and_transcribe(self, input_file):
        self.update_progress(25)  # Update the progress to 25% to indicate the start of processing.
        QApplication.processEvents()  
       
        # Initialize file paths for potential output files.
        mp3file = input_file.split(".")[0] + ".mp3"
        mp4file = input_file.split(".")[0] + ".mp4"
        filetype = input_file.split(".")[1]
        input_dir = os.path.dirname(input_file)
       
        try:
            if filetype in ("mp3", "wav"):
                # For audio files: convert to mp4 format and transcribe.
                output_directory = os.path.split(input_file)[0] + "/output"
                os.makedirs(output_directory, exist_ok=True)
                mp4file = os.path.join(output_directory, os.path.basename(input_file).replace(filetype, "mp4"))
                subprocess.run(["ffmpeg","-f","lavfi","-i","color=c=blue:s=1280x720","-i", input_file,"-shortest","-fflags","+shortest","-preset","ultrafast", mp4file])
                subprocess.run(["whisper", "--model en", mp4file, "--output_dir", output_directory])
                self.update_progress(50)  # Update progress to 50% after conversion.
                QApplication.processEvents()  
                directory,filename = os.path.split(input_file)
                tempFile = filename.split(".")[0]+".srt"
                temp2 = output_directory+ "/" + tempFile
                subFile= "subtitles="+ temp2
                captionedFile = temp2.replace(".srt","_Subtitled.mp4")
                subFile=subFile.replace(":/","\\\:\/")
                subprocess.run(["ffmpeg", "-i", mp4file, "-vf", subFile,"-c:v","libx264","-preset","ultrafast", "-crf","22","-c:a","copy",captionedFile])


            elif filetype in ("mp4", "mov"):
                output_directory = os.path.split(input_file)[0] + "/output"
                # For video files: extract audio, transcribe, and apply subtitles.
                subprocess.run(["ffmpeg", "-i", input_file, "-vn", "-codec:a", "libmp3lame", "-qscale:a", "4","-preset","ultrafast", mp3file])
                subprocess.run(["whisper", "--model en", mp3file, "--output_dir", output_directory])

                self.update_progress(50)  # Update progress midway through the operation.
                QApplication.processEvents()  

                # Apply generated subtitles to the original video.
                directory,filename = os.path.split(input_file)
                tempFile = filename.split(".")[0]+".srt"
                temp2 = output_directory+ "/" + tempFile
                subFile= "subtitles="+ temp2
                captionedFile = temp2.replace(".srt","_Subtitled.mp4")
                print(captionedFile)
                subFile=subFile.replace(":/","\\\:\/")
                subprocess.run(["ffmpeg", "-i", mp4file, "-vf", subFile,"-c:v","libx264","-preset","ultrafast", "-crf","22","-c:a","copy",captionedFile])

            self.update_progress(75)  # Update progress after transcription and subtitle application.
            QApplication.processEvents()

        except FileNotFoundError:
            # Handle the case where ffmpeg or whisper is not found on the system.
            self.label.setText("ffmpeg or whisper not found. Please install ffmpeg and whisper and try again.")
     
        self.update_progress(100)  # Finalize the progress to indicate completion of the task.

    def transcribe_directory(self):
        # Opens a directory selection dialog and processes each suitable media file found.
        directory = QFileDialog.getExistingDirectory(self, "Select Directory for Transcription")
        print(directory)
        if directory:
            for filename in os.listdir(directory):
                print(filename)
                if filename.endswith((".mp3", ".mp4", ".wav", ".mov")):
                    self.convert_and_transcribe(os.path.join(directory, filename))  

    '''Subtitle Handling'''

    def parse_subtitles(self, filename):
        # Initialize a list to hold subtitle blocks and timestamps.
        subtitles = []
        self.timeStamp = []  # List to hold timestamps
        srtFile = filename.split('.')[0] + '.srt'  # Construct the SRT filename.
        if os.path.exists(srtFile):  # Check if the SRT file exists.
            with open(srtFile, 'r') as file:  # Open the SRT file.
                content = file.read()  # Read the entire content of the file.
                blocks = content.split('\n\n')  # Split content into blocks separated by blank lines.
                for block in blocks:  # Iterate over each block.
                    parts = block.split('\n')  # Split block into individual lines.
                    if len(parts) >= 3:  # Check if block contains at least 3 lines (index, timestamps, subtitle text).
                        self.timeStamp.append(parts[1])  # Append timestamp for future use or debugging.
                        times = parts[1].split(' --> ')  # Split timestamp into start and end times.
                        start_time = self.time_to_milliseconds(times[0])  # Convert start time to milliseconds.
                        end_time = self.time_to_milliseconds(times[1])  # Convert end time to milliseconds.
                        text = '\n'.join(parts[2:])  # Join remaining parts as the subtitle text.
                        subtitles.append([start_time, end_time, text])  # Append subtitle block to the list.
        return subtitles  # Return the list of subtitles.                    

    def show_subtitles(self, filename):
        # Check if the subtitle file exists.
        if os.path.exists(filename):
            with open(filename, "r") as file:  # Open the file for reading.
                lines = file.readlines()  # Read all lines from the file.
            for line in lines:
                print(line.strip())  # Print each line, stripping trailing newlines.
        else:
            # If the file doesn't exist, display an error message in the text box.
            self.textBox.setPlainText("Subtitle file not found: " + filename)

    def onTextBoxEdit(self):
        # Triggered when the text box is edited. Checks if in edit mode and the media player is paused.
        if self.editMode and self.mediaPlayer.state() == QMediaPlayer.PausedState:
            self.userIsEditing = True  # Set a flag indicating the user is editing.

    def commitEdits(self):
        # Commits edits made to the text box if there's an active edit session.
        if self.currentlyEditingIndex is not None and self.userIsEditing:
            editedText = self.textBox.toPlainText()  # Extract edited text from the text box.
            self.subtitles[self.currentlyEditingIndex][2] = editedText  # Update the subtitles array with the edited text.
            self.userIsEditing = False  # Reset the editing flag.

    def update_subtitles(self):
        # Update the displayed subtitles based on the current playback position.
        current_time = self.mediaPlayer.position()  # Get current playback position in milliseconds.
        for i in range(len(self.subtitles)):
            start, end, text = self.subtitles[i]
            if start <= current_time < end:  # Check if current time is within the subtitle's time range.
                if self.currentlyEditingIndex is not None and self.editMode:
                    # If another subtitle was being edited, commit those edits before moving on.
                    if self.currentlyEditingIndex != i:
                        self.commitEdits()
                        self.userIsEditing = False
                if not self.userIsEditing or self.currentlyEditingIndex != i:
                    # Update the text box with the current subtitle and set the editing index.
                    self.textBox.setPlainText(text)
                    self.currentlyEditingIndex = i
                break  # Break the loop once the current subtitle is found and processed.
        else:
            # Clear the text box if no subtitles match the current time.
            self.textBox.clear()
            self.currentlyEditingIndex = None  # Reset the editing index.
            self.userIsEditing = False  # Reset the editing flag.

    def save_temporary_changes(self):
        # Saves the current subtitles to a temporary SRT file.
        if self.srt_filename:  # Check if SRT filename has been set.
            temp_filename = self.srt_filename.split('.')[0] + "_temp.srt"  # Construct temporary filename.
            with open(temp_filename, 'w') as file:  # Open temp file for writing.
                for i, subtitle in enumerate(self.subtitles):  # Iterate over subtitles.
                    # Write the subtitle index, timestamps, text, and an empty line for separation.
                    file.write(f"{i+1}\n{self.format_time(subtitle[0])} --> {self.format_time(subtitle[1])}\n{subtitle[2]}\n\n")
        else:
            # Show a warning message if no SRT filename is set.
            QMessageBox.warning(self, "Auto Save Failed", "No SRT filename set. Cannot save temporary changes.", QMessageBox.Ok)

    def export_changes(self):
        # Exports the edited subtitles and applies them to a new video file.
        if self.srt_filename:  # Ensure there's an SRT filename to work with.
            # Create filenames for the corrected SRT and MP4 files.
            corrected_filename = self.srt_filename.split('.')[0] + "_corrected.srt"
            captionedFile = os.path.join(os.path.dirname(self.srt_filename), self.srt_filename.split('.')[0] + "_corrected.mp4")
            # Check if the corrected MP4 file already exists.
            if os.path.exists(captionedFile):
                # Prompt the user to confirm overwriting the existing files.
                reply = QMessageBox.question(self, 'Confirm Overwrite', "Corrected files already exist. Do you want to overwrite them?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return  # Exit the function if user chooses not to overwrite.
            # Write the edited subtitles to the corrected SRT file.
            with open(corrected_filename, 'w') as file:
                for i, subtitle in enumerate(self.subtitles):
                    # Write the original timestamp, edited text, and an empty line for separation.
                    file.write(f"{i+1}\n{self.timeStamp[i]}\n{subtitle[2]}\n\n")
            # Use ffmpeg to apply the corrected subtitles to a new video file.
            corrected_filename=corrected_filename.replace(":/","\\\:\/")
            command = ["ffmpeg", "-y", "-i", self.filename, "-vf", f"subtitles={corrected_filename}", "-codec:a", "copy", captionedFile]
            subprocess.run(command)
            # Attempt to delete the temporary SRT file after export.
            temp_filename = self.srt_filename.split('.')[0] + "_temp.srt"
            try:
                os.remove(temp_filename)
                print(f"Temporary file {temp_filename} deleted successfully.")
            except OSError as e:
                print(f"Error: {e.filename} - {e.strerror}.")
        else:
            # Show a warning message if no SRT filename is set for export.
            QMessageBox.warning(self, "Export Failed", "No SRT filename set. Cannot export changes.", QMessageBox.Ok)

    def handle_timestamp_click(self, timestamp):
        # Seek the media player to the specified timestamp and display the corresponding subtitle text.
        self.mediaPlayer.setPosition(timestamp)  # Seek to timestamp.
        for subtitle in self.subtitles:  # Search for the subtitle with the matching timestamp.
            if subtitle[0] == timestamp:
                self.textBox.setPlainText(subtitle[2])  # Display the subtitle text.
                break  # Exit the loop once the matching subtitle is found.
 
    def toggleEditMode(self):
        # Toggles the edit mode, enabling or disabling text editing.
        if self.editMode:
            self.commitEdits()  # Commit any pending edits when leaving edit mode.
            self.exportChangesButton.setEnabled(True)  # Enable the export button when edits are committed.
        self.editMode = not self.editMode  # Toggle the edit mode state.
        self.textBox.setReadOnly(not self.editMode)  # Set the read-only state based on edit mode.
        # Change the text box background color to indicate edit mode.
        if self.editMode:
            self.textBox.setStyleSheet("background-color: lightyellow;")
        else:
            self.textBox.setStyleSheet("")  # Reset the style when not in edit mode.
         
    '''Video Playback Controls'''

    def seek_video(self, position):
        # Seek the media player to a specific position in milliseconds.
        self.mediaPlayer.setPosition(position)
   
    def play_video(self):
        # Toggle play/pause based on the current state of the media player.
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()  # Pause if currently playing.
        else:
            self.mediaPlayer.play()  # Play if paused or stopped.

    def start_over(self):
        # Restart video playback from the beginning.
        self.mediaPlayer.setPosition(0)  # Reset position to start.
        self.mediaPlayer.play()  # Begin playback immediately.

    def rewind_video(self):
        # Rewind the video by 1000 milliseconds (1 second).
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 1000)

    def fast_forward_video(self):
        # Fast forward the video by 1000 milliseconds (1 second).
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 1000)

    def update_video_duration(self, duration):
        # Set the range of the video scrubber to match the video's duration.
        self.videoScrubber.setRange(0, duration)  # Update range to video's full duration.
        self.videoScrubber.setValue(0)  # Reset the scrubber to the start position.

    def update_current_time_label(self, position):
        # Update the label displaying the current playback time.
        current_time = self.milliseconds_to_timestamp(position)  # Convert position to timestamp format.
        self.currentTimeLabel.setText(f"Current Time: {current_time}")  # Display formatted timestamp.
        self.videoScrubber.setValue(position)  # Update the video scrubber's position to match.

    def media_state_changed(self, state):
        # Update the play button icon based on the media player's state.
        if state == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))  # Show pause icon if playing.
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # Show play icon otherwise.

    '''Search and Results Handling'''

    def search_in_subtitles(self, keyword):
        # Searches for a keyword within the subtitles and collects the matching entries.
        results = []  # List to hold formatted results for display.
        timestamps = []  # List to hold start timestamps of matching subtitles for navigation.
        for subtitle in self.subtitles:
            # Check if the keyword is in the subtitle text, case-insensitively.
            if keyword.lower() in subtitle[2].lower():
                # Format the match as "start --> end\nText" for display.
                start_time = self.milliseconds_to_timestamp(subtitle[0])
                end_time = self.milliseconds_to_timestamp(subtitle[1])
                result_text = f"{start_time} --> {end_time}\n{subtitle[2]}"
                results.append(result_text)  # Add the formatted text to results.
                timestamps.append(subtitle[0])  # Add the start timestamp for navigation.
        return results, timestamps  # Return the lists of results and timestamps.
   
    def perform_search(self):
        # Initiates a search operation based on user input.
        if not self.subtitles:
            # Show a warning if there are no subtitles loaded.
            QMessageBox.warning(self, "Search Failed", "No subtitles loaded. Please load a video and its subtitles file first.", QMessageBox.Ok)
            return  # Exit the method if no subtitles are loaded.
        # Prompt the user to enter a search keyword.
        keyword, ok = QInputDialog.getText(self, 'Search Word', 'Enter the word to search:')
        if ok and keyword:  # Proceed if the user entered a keyword and clicked OK.
            results, timestamps = self.search_in_subtitles(keyword)  # Perform the search.
            # Show the search results in a custom dialog.
            self.show_search_results_with_messagebox(results, timestamps, keyword)

    def show_search_results_with_messagebox(self, results, timestamps, keyword):
        # Displays the search results in a custom dialog.
        dialog = ResultsDialog(results, timestamps, keyword, self)  # Create the dialog with results.
        dialog.timestampClicked.connect(self.handle_timestamp_click)  # Connect a signal to handle clicks on timestamps.
        dialog.exec_()  

    '''Combo Box and UI Updates'''

    def on_combobox_changed(self, index):
        # Handles actions based on the selected combobox option.
        if index == 1:  
            self.open_file()  # Call to open a file
        elif index == 2:  
            self.openFileNameDialog()  # Call to open a file dialog for transcription purposes.
        elif index == 3:
            self.transcribe_directory()  # Initiate batch transcription of all suitable files in a directory.
        elif index == 4:
            self.perform_search()  # Trigger the search functionality within loaded subtitles.
        self.comboBox.setCurrentIndex(0)  # Reset the combobox to its default state after an action is selected.

    def update_progress(self, value):
        # Updates the progress bar to the specified value.
        self.progress.setValue(value)  # Set the progress bar's current value.
        QApplication.processEvents()  # Ensure the UI updates to reflect the new progress bar value.      

class ResultsDialog(QDialog):
    #Define a signal for handling timestamp clicks
    timestampClicked = pyqtSignal(int)

    def __init__(self, results, timestamps, keyword, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Results")
        self.setGeometry(100, 100, 400, 300)

        #Initialize layout
        self.layout = QVBoxLayout(self)

        # Initialize the QTextEdit to display results
        self.resultsTextBox = QTextEdit(self)
        self.resultsTextBox.setReadOnly(True)
       
        # Process results to highlight the keyword
        highlighted_text = self.highlight_keyword(results, keyword)
        self.resultsTextBox.setHtml(highlighted_text)  # Use setHtml to apply HTML formatting
        self.layout.addWidget(self.resultsTextBox)

        #Close button
        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.prompt_for_more_search)
        self.layout.addWidget(self.closeButton)

        #Add clickable labels for timestamps
        for timestamp in timestamps:
            timestamp_label = QLabel(self.milliseconds_to_timestamp(timestamp))
            timestamp_label.setStyleSheet("color: blue; text-decoration: underline;")
            timestamp_label.setCursor(Qt.PointingHandCursor)  # Change cursor to hand pointer
            self.layout.addWidget(timestamp_label)
            # Connect click event to emit signal with the clicked timestamp
            timestamp_label.mousePressEvent = lambda event, t=timestamp: self.timestampClicked.emit(t)

    def prompt_for_more_search(self):
        #Prompt for more search
        reply = QMessageBox.question(self, "Continue Searching", "Do you want to search for more words?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent().perform_search()  # Calls perform_search of the parent
        self.close()

    def highlight_keyword(self, results, keyword):
        #Highlight keyword in results
        highlighted_results = []
        # Preparing the regular expression for case-insensitive search
        keyword_regex = re.compile(re.escape(keyword), re.IGNORECASE)
       
        for result in results:
            # Highlight keyword in the result using HTML mark tag
            highlighted_result = keyword_regex.sub(lambda match: f"<mark style='background-color: yellow;'>{match.group(0)}</mark>", result)
            highlighted_results.append(highlighted_result)
       
        return "<br>".join(highlighted_results)

    def milliseconds_to_timestamp(self, ms):
        #Convert milliseconds to timestamp format
        hours = ms // (1000 * 60 * 60)
        minutes = (ms // (1000 * 60)) % 60
        seconds = (ms // 1000) % 60
        milliseconds = ms % 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())

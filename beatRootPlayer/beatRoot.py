import numpy as np
import tkinter as tk
from tkinter import messagebox
import threading
from PIL import Image, ImageTk
import serial
import time
import statistics
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import client_data


class beatRoot:
    def __init__(self, root, ser):
        self.root = root
        self.root.title("beatRoot")
        self.root.configure(background='#d9d9d9')
        self.ser = ser
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_data.ID,
                                                            client_secret=client_data.SECRET,
                                                            redirect_uri=client_data.URI,
                                                            scope='user-read-playback-state,user-modify-playback-state'))

        # create ui elements
        self.logo = ImageTk.PhotoImage(Image.open("./beatroot.png").resize((586, 511)))
        self.logo_label = tk.Label(root, image=self.logo)

        self.manual_heart = tk.BooleanVar()
        self.heart_check = tk.Checkbutton(root, text="Enter Heartrate", command=self.enable_manual_in, variable=self.manual_heart)
        self.heart_entry = tk.Entry(root, state=tk.DISABLED)
        self.sensor_label = tk.Label(text="Sensor: ")
        self.heartrate_monitor = tk.Label(text="")

        self.song_label = tk.Label(root, text="Enter Song:")
        self.song_entry = tk.Entry(root)

        self.activity_label = tk.Label(root, text="Enter Activity:")
        self.activity_entry = tk.Entry(root)

        self.genre_label = tk.Label(root, text="Enter Genres (Optional):")
        self.genre_entry = tk.Entry(root)

        self.generate_button = tk.Button(root, text="Generate Playlist", background="grey", foreground="#1DD05D", command=self.generate_playlist)

        self.energy_label = tk.Label(root, text='')
        self.bpm_label = tk.Label(root, text='')

        self.result_label = tk.Label(root, text="")

        # media control
        self.play_img = ImageTk.PhotoImage(Image.open("./play.png").resize((100,114)))
        self.skip_img = ImageTk.PhotoImage(Image.open("./skip.png").resize((162,114)))
        self.rewind_img = ImageTk.PhotoImage(Image.open("./rewind.png").resize((162,114)))
        self.play_button = tk.Button(root, image=self.play_img, command=self.play_song)
        self.skip_button = tk.Button(root, image=self.skip_img, command=self.skip_song)
        self.rewind_button = tk.Button(root, image=self.rewind_img, command=self.rewind_song)

        # grid display
        self.logo_label.grid(row=0, column=2, columnspan=2, padx=5, pady=25)
        self.sensor_label.grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.heartrate_monitor.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        self.heart_check.grid(row=2, column=2, padx=5, pady=5, sticky='e')
        self.heart_entry.grid(row=2, column=3, padx=5, pady=5)
        self.song_label.grid(row=3, column=2, padx=5, pady=5, sticky="e")
        self.song_entry.grid(row=3, column=3, padx=5, pady=5)
        self.activity_label.grid(row=4, column=2, padx=5, pady=5, sticky="e")
        self.activity_entry.grid(row=4, column=3, padx=5, pady=5)
        self.genre_label.grid(row=5, column=2, padx=5, pady=5, sticky="e")
        self.genre_entry.grid(row=5, column=3, padx=5, pady=5)
        self.generate_button.grid(row=6, column=2, columnspan=2, pady=10)
        self.bpm_label.grid(row=6, column=2, padx=5, pady=5, sticky="w")
        self.energy_label.grid(row=6, column=3, padx=5, pady=5, sticky="e")
        self.result_label.grid(row=7, column=2, columnspan=2, pady=10)
        self.rewind_button.grid(row=8, column=0, padx=5, pady=5, sticky='e')
        self.play_button.grid(row=8, column=2, columnspan=2, padx=5, pady=5, sticky='s')
        self.skip_button.grid(row=8, column=4, padx=5, pady=5, sticky='w')

        self.heartrate = 0
        self.history = []
        self.playlist = []
        self.track_ids = {}
        self.ptr = 0
        # define target ranges of heart rate, danceability, and energy for each activity
        self.min_bpm = 60
        self.max_bpm = 150
        self.min_pulse = 40
        self.max_pulse = 180
        self.activities = {"meditation": [(40, 80), (0.2, 0.4), (0.2, 0.4)],
                       "study": [(60, 100), (0.3, 0.5), (0.4, 0.6)],
                       "walk": [(100, 120), (0.5,0.7), (0.6, 0.8)], # avg heart rate while walking is 100-120 bpm, avg walking speed is about 100-120 steps per min
                       "exercise": [(100, 165), (0.8, 1.0), (0.8, 1.0)]}
        

        self.sample_rate = 40
        self.sensor_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.sensor_thread.start()

    def enable_manual_in(self):
        """enables text entry box for heart rate"""
        if self.manual_heart.get():
            self.heart_entry.config(state=tk.NORMAL)
        else:
            self.heart_entry.config(state=tk.DISABLED)

    def update_heartrate_text(self):
        """updates ui with the sensor reading"""
        self.heartrate_monitor.config(text=str(self.heartrate))

    def read_serial(self):
        """read data from serial connection to arduino"""
        start = time.time()
        while True:
            if not int(time.time() - start) % self.sample_rate:
                if self.song_entry.get() != "" and self.activity_entry.get() != "":
                    self.generate_playlist()
            try:
                # setting default if a sensor is not attached 
                data = 100 

                if self.ser:
                    data = self.ser.readline().decode().strip()
                
                if data:
                    data = float(data)
                    self.history.append(data)
                    if self.check_hist(data):
                        self.heartrate = data
                        self.root.after(100, self.update_heartrate_text)
                        # print(self.heartrate)

            except UnicodeDecodeError as e:
                print(f"Error decoding data: {e}")

            time.sleep(1)


    def check_hist(self, data):
        """check incoming data from pulse sensor using a sliding window of previous readings and 2 stddevs around mean"""
        if len(self.history) >= 5:
            moving_average = statistics.mean(self.history[-5:])
            lower_thresh = max(self.min_pulse, moving_average - 2 * statistics.stdev(self.history))
            upper_thresh = min(self.max_pulse, moving_average + 2 * statistics.stdev(self.history))
        else:
            moving_average = 0
            lower_thresh = self.min_pulse
            upper_thresh = self.max_pulse
        self.history = self.history[-10:] if len(self.history) > 10 else self.history 
        return lower_thresh < data < upper_thresh


    def generate_playlist(self):
        """create playlist and update view accordingly"""
        song = self.song_entry.get()
        activity = self.activity_entry.get()
        genre = self.genre_entry.get()
        if self.manual_heart.get():
            self.heartrate = int(self.heart_entry.get())
        # print(bpm)

        if not song or not activity:
            messagebox.showerror("Invalid Input", "Please fill in song and activity")
            return
        if not genre:
            genre = ""

        self.set_playlist(song, genre, activity)
        self.result_label.config(text="Playlist:\n" + "\n".join(self.playlist))


    def set_playlist(self, song, genre, activity):
        """retrieve recommendations from spotify api based on user input"""
        if activity.lower() not in self.activities:
            messagebox.showerror("Invalid activity", "choose from: exercise, walk, study, meditation")
            return
        activity = activity.lower()

        bpm = self.heartrate # assign to bpm in case heartrate updates

        bpm_range = (40, 180)
        bpm_range = self.activities[activity][0]
        bpm_fraction = (bpm - bpm_range[0]) / (bpm_range[1] - bpm_range[0])

        dance_range = self.activities[activity][1]
        energy_range = self.activities[activity][2]

        # adjust danceability and energy based on heart rate
        adjusted_dance = dance_range[0] + bpm_fraction * (dance_range[1] - dance_range[0])
        adjusted_energy = energy_range[0] + bpm_fraction * (energy_range[1] - energy_range[0])

        # adjust the target bpm to search for based on user heart rate
        bpm_fraction = (self.heartrate - self.min_pulse) / (self.max_pulse - self.min_pulse)
        target_bpm = self.min_bpm + bpm_fraction * (self.max_bpm - self.min_bpm)

        # change color and add proper text to label
        color = "red" if bpm < self.activities[activity][0][0] or bpm > self.activities[activity][0][1] else "green"
        if bpm < np.mean(self.activities[activity][0]):
            arrow = "↑"
        elif bpm > np.mean(self.activities[activity][0]):
            arrow = "↓"
        else:
            arrow = ""
        
        self.bpm_label.config(text=f"{arrow}BPM{arrow}", fg=color)
        self.energy_label.config(text=f"{arrow}Energy{arrow}", fg=color)
        
        recommendations = self.sp.recommendations(
            seed_tracks=[self.get_track(song)],
            seed_genres=[g for g in ",".split(genre)] if genre else None,
            target_tempo=target_bpm,
            target_energy=adjusted_energy,
            target_danceability=adjusted_dance,
            limit=10
        )

        # show the song title and only the first three listed artists
        self.playlist = [f"{track['name']} - {', '.join(artist['name'] for artist in track['artists'][:3])}" for track in recommendations['tracks']]
        self.track_ids = {self.playlist[i] : x['id'] for i, x in enumerate(recommendations['tracks'])}
        self.ptr = 0


    def get_track(self, song):
        """find trackid by searching with the name of a song"""
        result = self.sp.search(q=song, type='track', limit=1)
        if result['tracks']['items']:
            # update text in the textbox with the result to show user
            self.song_entry.delete(0, tk.END)
            self.song_entry.insert(0, f"{result['tracks']['items'][0]['name']} - {result['tracks']['items'][0]['artists'][0]['name']}")
            return result['tracks']['items'][0]['id']
        else:
            messagebox.showerror("Track Not Found", f"The track '{song}' could not be found.")
            return None

    def play_song(self):
        try:
            if self.playlist and self.ptr < len(self.playlist):
                self.sp.start_playback(uris=[f"spotify:track:{self.track_ids[self.playlist[self.ptr]]}"])
        except spotipy.SpotifyException as e:
            messagebox.showerror("SpotifyException", "No active device found")

    def skip_song(self):
        if self.playlist:
            self.ptr += 1
            self.ptr %= len(self.playlist)
            self.play_song()

    def rewind_song(self):
        if self.playlist:
            self.ptr = max(0, self.ptr - 1)
            self.play_song()


if __name__ == "__main__":
    try:
        
        ## uncomment the following line if a heart rate sensor is attached
        #ser = serial.Serial("/dev/tty.usbmodem14101", 9600, timeout=0.1)

        ## comment the following line if a heart rate sensor is attached
        ser = None

        root = tk.Tk()
        beat = beatRoot(root, ser)
        root.mainloop()
    except serial.serialutil.SerialException as e:
        print(e)

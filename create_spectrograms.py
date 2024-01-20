from keras.models import load_model
from tensorflow.keras.models import Model
import matplotlib.pylab as plt
import librosa 
import numpy as np
from glob import glob 
import librosa.display 
import IPython.display as ipd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image
from scipy.spatial.distance import cosine
from pathlib import Path


def song_to_spectrogram(song_path,length_sec=30,save_image=True, save_name="spectrogram.png"):

    y, sr = librosa.load(song_path)
    y=y[:sr*length_sec  ]

    S = librosa.feature.melspectrogram(y=y, sr=sr,hop_length=512)
    S_DB = librosa.amplitude_to_db(S, ref=np.max)

    # Desired width in pixels
    desired_width = 336

    # Calculate the DPI needed to achieve the desired width
    dpi = int(desired_width / plt.figure(figsize=(desired_width / 80, 4)).get_figwidth())
    #plt.clf()

    width=desired_width / dpi
    fig=plt.figure(figsize=(width, width/3*2))
    librosa.display.specshow(S_DB, sr=sr,hop_length=512,
                             x_axis='time', y_axis='mel')
    plt.gca().set_axis_off()
    #plt.colorbar()
    #plt.savefig("spectrogram.png", bbox_inches='tight', pad_inches=0, transparent=False)
    #plt.title("Mel spectrogram", fontsize=20)
    #plt.show()
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    image_array = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')
    image_array = image_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    image = Image.fromarray(image_array)

    # Define the new size
    #new_size = (432, 288)  # Change this to your desired dimensions
    new_size = (129, 128)
    
    # Resize the image
    resized_image = image.resize(new_size, Image.LANCZOS)
    resized_image_data = np.array(resized_image)[:,:,:3]
    resized_image_data  = np.mean(resized_image_data, axis=2)
    #resized_image.show()  # Opens the image using the default viewer

    plt.close(fig)
    
    if save_image:
        resized_image.save(save_name)
        print("spectrogram saved at "+save_name)

    return resized_image_data

def create_spectrograms_for_dataset(dataset_dir, save_dir):
    songs = glob(dataset_dir + '*.wav')

    for s in songs:
        track_id = Path(s).stem.split("__")[1]
        save_path = save_dir+track_id+".png"
        song_to_spectrogram(s,length_sec=30,save_image=True, save_name=save_path)
        

dataset_dir = "Datasets/final_playlist/" 
save_dir = "Datasets/final_spectrograms/"
create_spectrograms_for_dataset(dataset_dir, save_dir)
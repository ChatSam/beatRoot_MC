import pyloudnorm as pyln
import noisereduce as nr
import soundfile as sf
from pydub import AudioSegment 
from pathlib import Path 
import glob
import librosa 

def convert_mp3_to_wav(src_path ,save_path):
    sound = AudioSegment.from_mp3(src_path)
    sound.export(save_path, format="wav")

def convert_mp3_to_wav_directory(src_directory):
    src_songs = glob(src_directory + "*.mp3")

    for s_path in src_songs:
        save_path = Path(s_path)
        save_path = save_path.with_suffix('.wav')
        convert_mp3_to_wav(s_path, save_path)

# preprocessing - Resample at 44100hz librosa default is 22050
def resample_audio(y, sr, target_sr=22050):
    new_y =librosa.resample(y, orig_sr=sr, target_sr=target_sr)
    return new_y

# TODOS: what is the optimal LUFS value?
# preprocessing - normalize loudness 
def norm_loudness(y, sr, lufs=-23.0):
    # measure
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(y)

    norm_audio = pyln.normalize.loudness(y, loudness, lufs)
    return norm_audio


# preprocessing - trim and pad 
def trim_audio(audio=None, src_file=None, start=0, duration=1):

    if src_file:
        audio = AudioSegment.from_file(src_file)

    song_duration = len(audio)
    end = start + duration

    if end > song_duration or start > song_duration:
        raise Exception(f"trim audio values out of bounds. max len is {song_duration}")
    
    trimmed_song = audio[start:end]
    return trimmed_song

# TODO: preprocessing - convert to mono audio
# def convert_to_mono(audio=None, src_file=None):
#     if src_file:
#         audio = AudioSegment.from_file(src_file)

#     samples = np.array(audio.get_array_of_samples())
#     return samples

# preprocessing - noise reduction
def reduce_noise(norm_y, sr):
    red_noise_y  = nr.reduce_noise(y=norm_y, sr=sr)
    return red_noise_y


def save_arr_to_wav(save_path, y,res):
    sf.write(save_path, y,res)


def preprocess_data(src_dir, save_dir):
    src_songs = glob(src_dir + "*.wav")

    for s_path in src_songs:
        f_name = Path(s_path).name
        save_path = save_dir + "pre_" + f_name

        y, sr = librosa.load(s_path)

        y_res_ref = resample_audio(y, sr)

        y_norm_ref = norm_loudness(y_res_ref,sr_ref)

        y_trim_ref = trim_audio(audio=y_norm_ref, start=4000, duration=1620000)
        #y_mono_ref = convert_to_mono(y_trim_ref)

        save_arr_to_wav(save_path, y_trim_ref, sr_ref) 

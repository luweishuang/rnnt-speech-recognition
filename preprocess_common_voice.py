from argparse import ArgumentParser
from pydub import AudioSegment
import multiprocessing
import os
import tensorflow as tf


def mp3_to_wav(filepath):
    try:
        audio_segment = AudioSegment.from_mp3(filepath)
        audio_segment.export('{}.wav'.format(filepath[:-4]), format='wav')
    except Exception:
        print(filepath, " ---> mp3_to_wav failed")
        pass
    os.remove(filepath)


def mp3_converter_job(mp3_filenames):
    for filename in mp3_filenames:
        if filename[-4:] != '.mp3':
            continue
        print(filename)
        mp3_to_wav(filename)


def main_preprocess(args):
    print('Converting all Common Voice MP3s to WAV...')
    clips_dir = os.path.join(args.data_dir, 'clips')
    all_clips = os.listdir(clips_dir)
    all_clips = [os.path.join(clips_dir, clip) for clip in all_clips]
    num_total = len(all_clips)
    num_cpus = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(num_cpus)
    job_size = num_total // num_cpus

    jobs = []
    for _ in range(num_cpus - 1):
        jobs.append(all_clips[:job_size])
        all_clips = all_clips[job_size:]
    jobs.append(all_clips)

    pool.map_async(mp3_converter_job, jobs)
    pool.close()
    pool.join()
    print('Removing missing files...')
    return


def read_file_test(filepath):
    try:
        audio_raw = tf.io.read_file(filepath)
        audio, sr = tf.audio.decode_wav(audio_raw)
    except:
        return False
    return True


def remove_missing(data_dir, fname, cnt_list):
    clips_dir = os.path.join(data_dir, 'clips')

    old_filepath = os.path.join(data_dir, '{}.tsv'.format(fname))
    new_filepath = os.path.join(data_dir, '{}-tmp.tsv'.format(fname))

    with open(old_filepath, 'r') as old_f:
        with open(new_filepath, 'w') as new_f:
            new_f.write(next(old_f))
            for line in old_f:
                audio_fn = line.split('\t')[1][:-4] + '.wav'
                cur_wav_file = os.path.join(clips_dir, audio_fn)
                if os.path.exists(cur_wav_file):
                    cnt_list[0] += 1
                    new_f.write(line)
                    # if read_file_test(cur_wav_file):
                    #     cnt_list[0] += 1
                    #     new_f.write(line)
                    # else:
                    #     print(cur_wav_file, " ----> read wav failed.")
                    #     os.remove(cur_wav_file)
                else:
                    print(audio_fn, " don't exist")

    os.remove(old_filepath)
    os.rename(new_filepath, old_filepath)


def check_file(args):
    tsv_files = ['dev', 'invalidated', 'other', 'test', 'train', 'validated']
    cnt_list = [0]
    for _file in tsv_files:
        remove_missing(args.data_dir, _file, cnt_list)
        print("cnt = %d " % cnt_list[0])      # 896452
    print("all cnt = %d " % cnt_list[0])  # 896452
    print('remove_missing Done.')



if __name__ == '__main__':
    ap = ArgumentParser()
    ap.add_argument('--data_dir', type=str, default='../data/en', help='Path to common voice data directory.')
    args = ap.parse_args()
    # main_preprocess(args)
    check_file(args)

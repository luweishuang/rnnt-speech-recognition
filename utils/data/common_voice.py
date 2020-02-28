import os
import tensorflow as tf

from .. import preprocessing


def tf_parse_line(line, data_dir):
    line_split = tf.strings.split(line, '\t')

    audio_fn = line_split[1]
    transcription = line_split[2]

    audio_filepath = tf.strings.join([data_dir, 'clips', audio_fn], '/')
    wav_filepath = tf.strings.substr(audio_filepath, 0, tf.strings.length(audio_filepath) - 4) + '.wav'

    if os.path.exists(wav_filepath):
        audio, sr = preprocessing.tf_load_audio(wav_filepath)
    else:
        print(wav_filepath, " don't exist")
    # audio, sr = preprocessing.tf_load_audio(wav_filepath)
    return audio, sr, transcription


def load_dataset(base_path, name):
    filepath = os.path.join(base_path, '{}.tsv'.format(name))
    with open(filepath, 'r') as f:
        dataset_size = sum(1 for _ in f) - 1

    dataset = tf.data.TextLineDataset([filepath])
    dataset = dataset.skip(1)
    dataset = dataset.map(lambda line: tf_parse_line(line, base_path), num_parallel_calls=tf.data.experimental.AUTOTUNE)
    return dataset, dataset_size


def texts_generator(base_path):
    split_names = ['dev', 'train', 'test']
    for split_name in split_names:
        with open(os.path.join(base_path, '{}.tsv'.format(split_name)), 'r') as f:
            for line in f:
                transcription = line.split('\t')[2]
                yield transcription
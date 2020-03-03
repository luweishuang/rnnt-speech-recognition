from absl import flags, logging, app
import os
import tensorflow as tf

from utils.data import common_voice
from utils import preprocessing, vocabulary, encoding
from utils import model as model_utils
from model import build_keras_model
from hparams import *

FLAGS = flags.FLAGS

# Required flags
flags.DEFINE_enum('mode', 'train', ['train', 'transcribe-file'], 'Mode to run.')
flags.DEFINE_string('data_dir', '../data/chinese', 'Input data directory.')
flags.DEFINE_string('test_file', 'test/common_voice_zh-CN_18909684.wav', 'wav file for test.')

# Optional flags
flags.DEFINE_string('tb_log_dir', './logs', 'Directory to save Tensorboard logs.')
flags.DEFINE_string('model_dir', './model', 'Directory to save model.')
flags.DEFINE_integer('batch_size', 32, 'Training batch size.')
flags.DEFINE_integer('n_epochs', 1000, 'Number of training epochs.')


def get_dataset_fn(base_path, 
                   encoder_fn, 
                   batch_size, 
                   hparams):
    def _dataset_fn(name):
        dataset, dataset_size = common_voice.load_dataset(base_path, name)
        dataset = preprocessing.preprocess_dataset(dataset, 
            encoder_fn=encoder_fn,
            batch_size=batch_size,
            hparams=hparams)
        steps_per_epoch = dataset_size // batch_size
        return dataset, steps_per_epoch
    return _dataset_fn


def train():
    hparams = {
        HP_TOKEN_TYPE: HP_TOKEN_TYPE.domain.values[0],
        HP_VOCAB_SIZE: HP_VOCAB_SIZE.domain.values[0],

        # Preprocessing
        HP_MEL_BINS: HP_MEL_BINS.domain.values[0],
        HP_FRAME_LENGTH: HP_FRAME_LENGTH.domain.values[0],
        HP_FRAME_STEP: HP_FRAME_STEP.domain.values[0],
        HP_HERTZ_LOW: HP_HERTZ_LOW.domain.values[0],
        HP_HERTZ_HIGH: HP_HERTZ_HIGH.domain.values[0],

        # Model
        HP_EMBEDDING_SIZE: HP_EMBEDDING_SIZE.domain.values[0],
        HP_ENCODER_LAYERS: HP_ENCODER_LAYERS.domain.values[0],
        HP_ENCODER_SIZE: HP_ENCODER_SIZE.domain.values[0],
        HP_TIME_REDUCT_INDEX: HP_TIME_REDUCT_INDEX.domain.values[0],
        HP_TIME_REDUCT_FACTOR: HP_TIME_REDUCT_FACTOR.domain.values[0],
        HP_PRED_NET_LAYERS: HP_PRED_NET_LAYERS.domain.values[0],
        HP_JOINT_NET_SIZE: HP_JOINT_NET_SIZE.domain.values[0],
        HP_SOFTMAX_SIZE: HP_SOFTMAX_SIZE.domain.values[0],

        HP_LEARNING_RATE: HP_LEARNING_RATE.domain.values[0]
    }

    if os.path.exists(os.path.join(FLAGS.model_dir, 'hparams.json')):
        _hparams = model_utils.load_hparams(FLAGS.model_dir)
        encoder_fn, vocab_size = encoding.load_encoder(FLAGS.model_dir, hparams=_hparams)
        model, loss_fn = model_utils.load_model(FLAGS.model_dir, vocab_size=vocab_size, hparams=_hparams)
    else:
        _hparams = {k.name: v for k, v in hparams.items()}
        texts_gen = common_voice.texts_generator(FLAGS.data_dir)
        encoder_fn, vocab_size = encoding.build_encoder(texts_gen, model_dir=FLAGS.model_dir, hparams=_hparams)
        model, loss_fn = build_keras_model(vocab_size, _hparams)
    logging.info('Using {} encoder with vocab size: {}'.format(_hparams[HP_TOKEN_TYPE.name], vocab_size))
    dataset_fn = get_dataset_fn(FLAGS.data_dir, 
        encoder_fn=encoder_fn,
        batch_size=FLAGS.batch_size,
        hparams=hparams)

    train_dataset, train_steps = dataset_fn('train')
    dev_dataset, dev_steps = dataset_fn('dev')
    optimizer = tf.keras.optimizers.Adam(_hparams[HP_LEARNING_RATE.name])
    model.compile(loss=loss_fn, optimizer=optimizer, experimental_run_tf_function=False)

    os.makedirs(FLAGS.model_dir, exist_ok=True)
    checkpoint_fp = os.path.join(FLAGS.model_dir, 'model.{epoch:03d}-{val_loss:.4f}.hdf5')
    model_utils.save_hparams(_hparams, FLAGS.model_dir)
    model.fit(train_dataset,
        epochs=FLAGS.n_epochs,
        steps_per_epoch=train_steps,
        validation_data=dev_dataset,
        validation_steps=dev_steps,
        callbacks=[
            tf.keras.callbacks.TensorBoard(FLAGS.tb_log_dir),
            tf.keras.callbacks.ModelCheckpoint(checkpoint_fp, save_weights_only=True)
        ])


def transcribe_file():
    if os.path.exists(os.path.join(FLAGS.model_dir, 'hparams.json')):
        _hparams = model_utils.load_hparams(FLAGS.model_dir)
        encoder_fn, vocab_size = encoding.load_encoder(FLAGS.model_dir, hparams=_hparams)
        model, loss_fn = model_utils.load_model(FLAGS.model_dir, vocab_size=vocab_size, hparams=_hparams)
        optimizer = tf.keras.optimizers.Adam(_hparams[HP_LEARNING_RATE.name])
        model.compile(loss=loss_fn, optimizer=optimizer, experimental_run_tf_function=False)
    else:
        print('need afford model_dir ')
        return
    transcription = model.predict(FLAGS.test_file)
    print('Input file: {}'.format(FLAGS.input))
    print('Transcription: {}'.format(transcription))


def main(_):
    if FLAGS.mode == 'train':
        train()
    elif FLAGS.mode == 'transcribe-file':
        transcribe_file()


if __name__ == '__main__':
    app.run(main)

# -*- coding: utf-8 -*-
import os
import sys
import time
import json

import tensorflow as tf

import datagen as dg
from sample import sample_sequence
from model import default_hparams, get_train_ops

def _print_decoded(outputs, idx_to_char, logs):
    for i in range(outputs.shape[0]):
            text = ''.join([idx_to_char[x] for x in outputs[i]])
            log(i, logs)
            log(text, logs)

def log(msg, logs, nl=True):
    if not type(logs) == list:
        logs = [logs]
    for l in logs:
        l.write(str(msg))
        if nl:
            l.write('\n')

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str, help="path to the text corpus")
    parser.add_argument('-m', '--modelpath', type=str, default="models/", help="path under which model checkpoints will be saved")
    parser.add_argument('-p', '--hparams', type=str, help="path to json-stored hyperparams")
    parser.add_argument('--sample_steps', type=int, default=5000, help="sample model after how many steps")
    parser.add_argument('--save_steps', type=int, default=5000, help="save model after how many steps")
    parser.add_argument('--log_steps', type=int, default=100, help="log output to stdout after how many steps")
    parser.add_argument('-v', '--verbose', action='store_true', help="if present, prints samples generated while training to stdout")
    parser.add_argument('--log_dir', type=str, default='logs/', help='directory to store tensorboard logs')
    args = parser.parse_args()

    hp = default_hparams()
    hp.sample_every = args.sample_steps
    if args.hparams is not None:
        with open(args.hparams, 'r') as hf:
            hp.parse_json(hf.read())

    fname = args.infile

    cti = dg.make_char_to_idx(fname)
    itc = {v: k for k, v in cti.items()}

    hp.n_vocab = len(cti)

    batch_size = hp.batch_size
    total_chars = dg.get_char_count(fname)

    # need to estimate the number of parameter updates durning the entire training because of
    # an intricate learning rate adaptation scheme without which are transformers hard to train
    total_updates = ((total_chars - (hp.n_ctx + 1)) // hp.stride + 1) // batch_size * hp.n_epochs
    hp.n_updates_total = total_updates

    context = tf.placeholder(tf.int32, [batch_size, None])
    labels = tf.placeholder(tf.int32, [batch_size, None])

    loss, train_ops = get_train_ops(hp, context, labels, past=None)

    output = sample_sequence(hparams=hp,
                            length=hp.n_ctx // 2,
                            context=context,
                            batch_size=batch_size,
                            temperature=1,
                            top_k=5)

    # sample / save / log every N steps
    sample_steps = hp.sample_every
    save_steps = args.save_steps
    log_steps = args.log_steps
    steps = 0

    primed_text = "honza 12. brezen 2000"
    primed_text = [cti[c] for c in primed_text]

    saver = tf.train.Saver(max_to_keep=5)
    signature = str(int(time.time())) # model signature

    # log files for model's loss and intermediate samples
    trainf = open('train_%s.txt' % signature, 'w', encoding='utf-8')
    logs = [trainf, sys.stdout] if args.verbose else [trainf]
    # create log_dir if not already created
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for e in range(hp.n_epochs):
            # tensorboard
            summaries = tf.summary.merge_all()
            writer = tf.summary.FileWriter(
                os.path.join(args.log_dir, time.strftime("%Y-%m-%d-%H-%M-%S")))
            writer.add_graph(sess.graph)

            g = dg.data_iterator(fname, cti, buffer=65536, context=hp.n_ctx, batch=batch_size, stride=8)

            # this is really stupid but i dont know how to count the amount of batches the generator yields
            # list(g) for some reason doesnt work for training, so i have to do it on a duplicate generator with the same params
            gg = dg.data_iterator(fname, cti, buffer=65536, context=hp.n_ctx, batch=batch_size, stride=8)
            total_batches = len(list(gg))

            for batch in g:
                start = time.time()
                # compute loss on batch and update params
                summ, l, _ = sess.run((summaries, loss, train_ops), feed_dict={context: batch['features'], labels: batch['labels']})
                # tensorboard
                writer.add_summary(summ, steps)
                # tensorboardcolab
                tb.save_value('Train Loss', 'train_loss', steps, l)
                tb.flush_line('train_loss')

                # sample model every sample_steps
                if ((steps > 0) & (steps % sample_steps == 0)):
                    log("================= Sampling | {} steps | epoch {} =================".format(steps, e + 1), logs)
                    out = sess.run(output, feed_dict={context: batch_size * [primed_text]})
                    _print_decoded(out, itc, logs)

                # log process to stdout every log_steps
                if steps % log_steps == 0:
                    end = time.time()
                    print("{}/{} (epoch {}), train_loss = {:.3f}, time/batch = {:.3f}"
                      .format(steps,
                      hp.n_epochs * total_batches,
                      e, l, end - start))

                # save model every save_steps
                if ((steps > 0) & (steps % save_steps == 0)):
                    print("Saving model..")
                    if not os.path.exists(args.modelpath):
                        os.makedirs(args.modelpath)
                    ckpt_path = os.path.join(args.modelpath, signature + '.ckpt')
                    saver.save(sess, ckpt_path, global_step=e)

                # increment steps
                steps += 1

        log("================= End of training | Final samples =================", logs)
        out = sess.run(output, feed_dict={context: batch_size * [primed_text]})
        _print_decoded(out, itc, logs)

    # coda
    with open('vocab.json', 'w', encoding='utf-8') as f:
        json.dump(cti, f)
    with open('hparams.json', 'w') as f:
        f.write(hp.to_json())

    trainf.close()

if __name__ == "__main__":
    main()

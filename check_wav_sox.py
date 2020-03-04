import os
import math


def get_wav_duration(wav_path):
    cmd = "sox {} -n stat 2>&1".format(wav_path)
    tmp = os.popen(cmd)
    dur_line = tmp.readlines()[1].split()
    dur = math.floor(float(dur_line[2]) * 10)/10
    return str(dur)


wavdir = '../data/en/clips'
rm_cnt = 0
for wav_id in os.listdir(wavdir):
    if wav_id.endswith("wav") or wav_id.endswith("WAV"):
        cur_wav_file = os.path.join(wavdir, wav_id)
        duration = get_wav_duration(cur_wav_file)
        if 0.0 == float(duration):
            # print(duration)
            # print('0.0 == float(duration)')
            os.remove(cur_wav_file)
            rm_cnt += 1
print('total remove cnt = %d ' % rm_cnt)

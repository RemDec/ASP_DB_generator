import random
import string


def generator_rdm_int(min_val=0, max_val=100000):
    return lambda _: str(random.randint(min_val, max_val))


def get_generator_rdm_int(min_val=0, max_val=100000):
    return lambda _: generator_rdm_int(min_val=min_val, max_val=max_val)


def generator_rdm_str(str_length=8):
    return lambda _: ''.join(random.choices(string.ascii_uppercase + string.digits, k=str_length))


def get_generator_rdm_str(str_length=8):
    return lambda _: generator_rdm_str(str_length=str_length)


def generator_increment_int(incr_val=1, start_val=1):
    i = start_val - 1
    while True:
        i += incr_val
        yield i


def get_generator_increment_int(incr_val=1, start_val=1):
    return lambda _: generator_increment_int(incr_val=incr_val, start_val=start_val)


def generator_increment_str(incr_val=1, start_length=5, letters=string.ascii_lowercase):
    start_letter = letters[0]
    size = len(letters)
    i = [start_letter]*start_length  # list to mute it on the fly
    yield ''.join(i)
    while True:
        rank = len(i)-1
        while rank > -1:
            ind_letter_at_rank = letters.index(i[rank])
            ind_new = ind_letter_at_rank + incr_val
            if ind_new >= size:
                # need to report increment on next rank
                i[rank] = letters[ind_new % size]
                rank -= 1
            else:
                # increment letter at current rank
                i[rank] = letters[ind_new]
                yield ''.join(i)
        # need to extend the string
        i = [start_letter] + i
        yield ''.join(i)


def get_generator_increment_str(incr_val=1, start_length=5, letters=string.ascii_lowercase):
    return lambda _: generator_increment_str(incr_val=incr_val, start_length=start_length, letters=letters)


def generator_word(dict_path="/etc/dictionaries-common/words", min_len=4, rdm=False):
    with open(dict_path, 'r') as fp:
        words = fp.readlines()
    nbr = len(words)
    i = 0
    if rdm:
        random.shuffle(words)
    if len(words) > 0:
        while True:
            word = words[i].strip()
            if len(word) >= min_len:
                yield word
            i = (i + 1) % nbr
    while True:
        yield "word"


def get_generator_word(dict_path="/etc/dictionaries/common/words", min_len=4, rdm=False):
    return lambda _: generator_word(dict_path=dict_path, min_len=min_len, rdm=rdm)


def generator_rdm_bool(numeric=True):
    if numeric:
        return lambda _: str(random.randint(0, 1))
    return lambda _: str(random.getrandbits(1))


def get_generator_rdm_bool(numeric=True):
    return lambda _: generator_rdm_bool(numeric=numeric)


if __name__ == "__main__":
    gen_fct = generator_increment_int()
    gen_fct2 = generator_increment_str(letters='ab')
    print([next(gen_fct) for i in range(10)])
    print([next(gen_fct2) for i in range(10)])
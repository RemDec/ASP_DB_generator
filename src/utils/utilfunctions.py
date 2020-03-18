

def single_to_tuple(elmt, convert_to_str=True):
    try:
        if not isinstance(elmt, str):
            iter(elmt)
            return tuple(map(str, elmt) if convert_to_str else elmt)
    except TypeError:
        pass
    # single element string or not iterable transformed into tuple of arity 1
    return elmt,


def get_indexes(base, find_in):
    indexes = []
    for elmt in base:
        try:
            indexes.append(find_in.index(elmt))
        except ValueError:
            pass
    return indexes


if __name__ == "__main__":
    print(single_to_tuple("abc"), single_to_tuple(3), single_to_tuple(["ab", "cd"]), single_to_tuple((1, 2)), sep='  ')
    print(get_indexes(["attr1", "attr0", "attrY"], ["attr0", "attr2", "attr1", "attrX"]))
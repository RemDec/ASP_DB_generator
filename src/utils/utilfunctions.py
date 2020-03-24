

def single_to_tuple(elmt, convert_to_str=True):
    try:
        if not isinstance(elmt, str):
            iter(elmt)
            return tuple(map(str, elmt) if convert_to_str else elmt)
    except TypeError:
        pass
    # single element string or not iterable transformed into tuple of arity 1
    return elmt,


def stringify_given_attr(given_attr_value):
    stringed = {}
    for attr, val in given_attr_value.items():
        stringed[str(attr)] = str(val)
    return stringed


def fill_tuple_dflt_vals(given_tuple, dflt_vals):
    from_ind = len(given_tuple)
    for i in range(from_ind, len(dflt_vals)):
        given_tuple = given_tuple + (dflt_vals[i],)
    return given_tuple


def normalize_gen_param(param_generation):
    # return [(nbr, given_attr_vals1), (nbr2, given_attr_vals2), ...]
    if isinstance(param_generation, int):
        return [(param_generation, {})]
    elif isinstance(param_generation, tuple):
        if len(param_generation) >= 2:
            return [(param_generation[0], stringify_given_attr(param_generation[1]))]
        else:
            raise ValueError(f"Length of tuple given in generation parameter is != 2 ({param_generation})")
    elif isinstance(param_generation, dict):
        return [(1, stringify_given_attr(param_generation))]
    elif isinstance(param_generation, list):
        normalized = []
        for param in param_generation:
            normalized.extend(normalize_gen_param(param))
        return normalized


def get_indexes(base, find_in):
    indexes = []
    for elmt in base:
        try:
            indexes.append(find_in.index(elmt))
        except ValueError:
            pass
    return indexes


def write_db_inst(dbinst, asp=True, printed=False, target_dir=".", target_file="database"):
    from pathlib import Path
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    filepath_asp = f"{target_dir}/ASP_{target_file}"
    filepath_print = f"{target_dir}/PRINT_{target_file}"

    def write_it(path, s):
        with open(path, 'w+') as fp:
            fp.write(s)
    if asp:
        write_it(filepath_asp, dbinst.repr_ASP())
    if printed:
        write_it(filepath_print, str(dbinst))


if __name__ == "__main__":
    print(single_to_tuple("abc"), single_to_tuple(3), single_to_tuple(["ab", "cd"]), single_to_tuple((1, 2)), sep='  ')
    print(get_indexes(["attr1", "attr0", "attrY"], ["attr0", "attr2", "attr1", "attrX"]))
    params = [5, 10, (1, {"attr": "val"}), 7, (9, {"attr2": "val2", "attr3": "val3"}), [88, (78, {})], {"aX": "valY"}]
    print(normalize_gen_param(params))
    print(fill_tuple_dflt_vals((0, 1), (None, None, "toadd", "tadd2")))
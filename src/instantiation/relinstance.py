from src.utils.utilfunctions import get_indexes
from operator import add, sub, itemgetter
from functools import reduce
import random


class SchemaError(ValueError):

    def __init__(self, msg, schema):
        super().__init__(msg)
        self.schema = schema


class RelationInstance:

    def __init__(self, rel_model, attribute_fix, init_tuples=None):
        self.rel_model = rel_model
        self.name = rel_model.name
        self.attribute_fix = attribute_fix
        self.tuples = []
        self.nbr_generated = 0
        self.nbr_constrained = 0
        self.nbr_degenerated = 0
        if init_tuples is not None:
            self.feed_tuples(init_tuples)

    def feed_tuples(self, tuples, from_constraint=False, degenerated=False):
        tuples = [tuples] if not isinstance(tuples, list) else tuples
        formated_tuples = []
        for one_tuple_base in tuples:
            only_values = []
            for i, attr_val in enumerate(one_tuple_base):
                if isinstance(attr_val, tuple):  # so first item should be attribute name
                    if not attr_val[0] == self.attribute_fix[i]:
                        err = f"A given tuple attribute name {attr_val[0]} doesn't fit fixed attribute schema"
                        raise SchemaError(err, self.attribute_fix)
                    # get the value corresponding to attribute
                    only_values.append(attr_val[1])
                else:
                    only_values.append(attr_val)
            formated_tuples.append((tuple(only_values), from_constraint, degenerated))
        self.tuples.extend(formated_tuples)
        self.adjust_tuple_nbrs(len(formated_tuples), from_constraint, degenerated)

    def generate_new_tuple(self, given_attr_values, keep_attr_name=False, purge_existing=True, tuples_to_insert=None):
        tuples_to_insert = [] if tuples_to_insert is None else tuples_to_insert  # grouped adding, detect duplicate
        generated_tuple = self.rel_model.generate_tuple(given_attr_values, self.attribute_fix, keep_attr_name)
        if purge_existing:
            indexes_pk_in_fix = self.get_indexes_in_fixed_attr()
            # get values from the generated tuples for attributes in the fixed ones also in the PK from the relation
            values_gen_for_pk = itemgetter(*indexes_pk_in_fix)(generated_tuple)
            if keep_attr_name:
                values_gen_for_pk = itemgetter(1)(values_gen_for_pk)
            for tup in tuples_to_insert:
                if itemgetter(*indexes_pk_in_fix)(tup) == values_gen_for_pk:
                    return None  # Duplicate from the PK point of view
            for tup, _, _ in self.tuples:
                if itemgetter(*indexes_pk_in_fix)(tup) == values_gen_for_pk:
                    return None  # Duplicate from the PK point of view
        return generated_tuple

    def generate_new_tuples(self, given_attr_values_list, keep_attr_name=False, purge_existing=True):
        gen_tuples = []
        for given_vals in given_attr_values_list:
            generated_tuple = self.generate_new_tuple(given_vals, keep_attr_name=keep_attr_name,
                                                      purge_existing=purge_existing, tuples_to_insert=gen_tuples)
            if generated_tuple is not None:
                gen_tuples.append(generated_tuple)
        return gen_tuples

    def generate_and_feed_tuples(self, given_attr_values_list, from_constraint=False, degenerated=False,
                                 respect_fk_constraint=True, purge_existing=True):
        generated = self.generate_new_tuples(given_attr_values_list, purge_existing=purge_existing)
        self.feed_tuples(generated, from_constraint, degenerated)
        # if some fixed attributes constitute a FK, should return tuples to respect it
        if not respect_fk_constraint:
            return generated, {}
        o_rel_tuples_fk = {}  # to feed as {Relation: [{attr1: val1,..}, {attr1: val1,..}], Relation2: [FK attr vals], }
        for ind_attr_fk, rel in self.get_ind_fixed_attr_in_fk().items():
            for tup in generated:
                # keep subset of generated tuple values considering only attributes in FK referencing rel
                tup_fk_val = itemgetter(*ind_attr_fk)(tup)
                tup_fk_attr = itemgetter(*ind_attr_fk)(self.attribute_fix)
                dict_attr_val = {}
                for ind in range(len(ind_attr_fk)):
                    # rebuilding unordered dict {attr1: val1, attr2: val2, ..} where attrN belongs to FK to rel
                    attr, val = tup_fk_attr[ind], tup_fk_val[ind]
                    dict_attr_val[attr] = val
                if o_rel_tuples_fk.get(rel) is None:
                    o_rel_tuples_fk[rel] = [dict_attr_val]
                else:
                    o_rel_tuples_fk[rel].append(dict_attr_val)
        return generated, o_rel_tuples_fk

    def adjust_tuple_nbrs(self, nbr, from_constraint, degenerated, adding=True):
        # Neither from_constraint nor degenerated -> regular generation
        # From_constraint -> generated from another relation, added here to respect FK (+ eventually gen missing attr)
        # Degenerated -> degeneration of actual tuple in this instance
        # From_constraint & degenerated -> result of another relation degeneration on attributes related to FK
        #                                  referencing this relation, then adding new tuples here to respect FK
        op = add if adding else sub
        if not(from_constraint or degenerated):
            self.nbr_generated = op(self.nbr_generated, nbr)
        if from_constraint:  # added to this relation instance to respect FK, whether from a degeneration or not
            self.nbr_constrained = op(self.nbr_constrained, nbr)
        if not from_constraint and degenerated:  # degeneration of this instance
            self.nbr_degenerated = op(self.nbr_degenerated, nbr)

    def get_tuples(self, nbr, only_values=True, selector=lambda tuple_info: True, rdm=False):
        result = []
        indexes = range(self.get_size())
        if rdm:
            random.shuffle(indexes)
        for i in range(min(nbr, self.get_size())):
            test_tuple = self.tuples[indexes[i]]
            if selector(test_tuple):
                result.append(test_tuple[0] if only_values else test_tuple)
        return result

    def get_indexes_in_fixed_attr(self, target_attr=None):
        target_attr = self.rel_model.get_pk_attr() if target_attr is None else target_attr
        return get_indexes(target_attr, self.attribute_fix)

    def get_ind_fixed_attr_in_fk(self):
        in_fk = {}
        for fk, rel in self.rel_model.fks.items():
            all_fk_attr_in_fix = []
            for attr in fk:
                try:
                    all_fk_attr_in_fix.append(self.attribute_fix.index(attr))
                except ValueError:
                    all_fk_attr_in_fix = False
                    break
            if all_fk_attr_in_fix:
                in_fk[tuple(all_fk_attr_in_fix)] = rel
        return in_fk

    def get_size(self):
        return len(self.tuples)

    def get_rel_model(self):
        return self.rel_model

    def get_fixed_attributes(self):
        return self.attribute_fix

    def repr_n_tuples(self, tuples, n=10):
        max_lens = []
        sel_tuples = tuples[:n]
        attributes = [f"[{attr}]" if self.rel_model.pk_contains(attr) else attr for attr in self.attribute_fix]
        for col, attr_name in enumerate(attributes):
            col_attr = [tup[0][col] for tup in sel_tuples]
            max_width_tup_val = reduce(lambda c, s: max(c, len(s)), col_attr, -1)
            width = max(len(attr_name), max_width_tup_val)
            max_lens.append(width)
        s = f"{self.rel_model.name} "
        shifting = len(s)
        s += '|'
        info_header = " C D "
        for i, attr_name in enumerate(attributes):
            spaces = ' '*(max_lens[i]-len(attr_name))
            info_header += f" {attr_name}{spaces}"
        s += f"{info_header}\n"
        s += f"{' '*shifting}+{'-'*len(info_header)}\n"
        for tuple_val, from_constraint, degenerated in sel_tuples:
            repr_c = '*' if from_constraint else ' '
            repr_d = '*' if degenerated else ' '
            s += f"{' '*shifting}| {repr_c} {repr_d} "
            for i, attr_val in enumerate(tuple_val):
                spaces = ' '*(max_lens[i]-len(attr_val))
                s += f" {attr_val}{spaces}"
            s += '\n'
        return s

    def repr_ASP(self):
        fact_name = self.rel_model.name.lower()
        s = ""
        for tup in self.tuples:
            s += f"{fact_name}({','.join(tup[0]).lower()}).\n"
        return s

    def __str__(self):
        s = f"Instance of {self.rel_model.name}, {self.get_size()} tuples : {self.nbr_generated} (regular)" \
            f" {self.nbr_constrained} (from constraints) {self.nbr_degenerated} (degenerated)\n"
        return s + self.repr_n_tuples(self.tuples, self.get_size())


if __name__ == "__main__":
    from src.model.relation import Relation
    from src.model.attribute import AttributeInfo, AttributeTypes
    SRel = Relation("SRel", pk="pk",
                    attributes={"pk": AttributeInfo("pk"),
                                "attr1": AttributeInfo("attr1", attr_type=AttributeTypes.incr_str)})
    inst = RelationInstance(SRel, attribute_fix=["pk", "attr1"])
    inst.feed_tuples([[("pk", '1'), ("attr1", 'valueeeee')], ['2', "longvalforattr1"]])
    inst.feed_tuples(('3', "from_constraint"), from_constraint=True)
    inst.feed_tuples([('4', "degenerated")], degenerated=True)

    print(inst)
    print(inst.generate_new_tuple(given_attr_values={"pk": '1'}))

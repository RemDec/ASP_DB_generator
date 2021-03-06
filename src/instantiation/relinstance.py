from src.utils.utilfunctions import get_indexes
from operator import add, sub, itemgetter
from functools import reduce
import random


class SchemaError(ValueError):

    def __init__(self, msg, schema):
        super().__init__(msg)
        self.schema = schema


class RelationInstance:

    def __init__(self, rel_model, attribute_fix):
        self.rel_model = rel_model
        self.name = rel_model.name
        self.attribute_fix = attribute_fix
        self.tuples = []
        self.nbr_generated = 0
        self.nbr_constrained = 0
        self.nbr_degenerated = 0

    # ---- TUPLES GENERATION AND FEEDING ----

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

    def generate_new_tuple(self, given_attr_values, keep_attr_name=False, respect_pk=True, o_tuples_to_insert=None):
        o_tuples_to_insert = [] if o_tuples_to_insert is None else o_tuples_to_insert  # in case grouped insertion
        generated_tuple = self.rel_model.generate_tuple(given_attr_values, self.attribute_fix, keep_attr_name)
        if respect_pk:
            indexes_pk_in_fix = self.get_indexes_in_fixed_attr()
            # get values from the generated tuples for attributes in the fixed ones also in the PK from the relation
            values_gen_for_pk = itemgetter(*indexes_pk_in_fix)(generated_tuple)
            if keep_attr_name:
                values_gen_for_pk = itemgetter(1)(values_gen_for_pk)
            for tup in o_tuples_to_insert:
                if itemgetter(*indexes_pk_in_fix)(tup) == values_gen_for_pk:
                    return None  # Duplicate from the PK point of view
            for tup, _, _ in self.tuples:
                if itemgetter(*indexes_pk_in_fix)(tup) == values_gen_for_pk:
                    return None  # Duplicate from the PK point of view
        return generated_tuple

    def generate_new_tuples(self, given_attr_values_list, keep_attr_name=False, respect_pk=True):
        gen_tuples = []
        for given_vals in given_attr_values_list:
            generated_tuple = self.generate_new_tuple(given_vals, keep_attr_name=keep_attr_name,
                                                      respect_pk=respect_pk, o_tuples_to_insert=gen_tuples)
            if generated_tuple is not None:
                gen_tuples.append(generated_tuple)
        return gen_tuples

    def generate_and_feed_tuples(self, given_attr_values_list, from_constraint=False, degenerated=False,
                                 respect_fk_constraint=True, respect_pk=True):
        generated = self.generate_new_tuples(given_attr_values_list, respect_pk=respect_pk)
        self.feed_tuples(generated, from_constraint, degenerated)
        # if some fixed attributes constitute a FK, should return tuples to respect it
        if not respect_fk_constraint:
            return generated, {}
        o_rel_fk_attr_values = self.generate_fk_attr_vals(generated)
        return generated, o_rel_fk_attr_values

    # ---- TUPLES DEGENERATION ----

    def form_given_attr_values(self, from_tuple, fixed_attrs_list):
        given_attr_vals = {}
        indexes = self.get_indexes_in_fixed_attr(fixed_attrs_list)
        for ind in indexes:
            attr_name = self.attribute_fix[ind]
            given_attr_vals[attr_name] = from_tuple[ind]
        return given_attr_vals

    def degenerate_tuples_at_inds(self, indexes, fixed_attrs=None):
        if fixed_attrs is None:
            pk_indexes = self.get_indexes_in_fixed_attr()
            fixed_attrs = itemgetter(*pk_indexes)(self.attribute_fix)
            if not isinstance(fixed_attrs, tuple):
                fixed_attrs = (fixed_attrs,)
        given_attr_vals_list = []
        for ind in indexes:
            given_attr_vals_list.append(self.form_given_attr_values(self[ind][0], fixed_attrs))
        return self.generate_new_tuples(given_attr_vals_list, respect_pk=False)

    def degenerate_and_feed_tuples_at_inds(self, indexes, fixed_attrs=None, respect_fk_constraints=True):
        degenerated = self.degenerate_tuples_at_inds(indexes, fixed_attrs=fixed_attrs)
        self.feed_tuples(degenerated, from_constraint=False, degenerated=True)
        if not respect_fk_constraints:
            return degenerated, {}
        o_rel_fk_attr_values = self.generate_fk_attr_vals(degenerated)
        return degenerated, o_rel_fk_attr_values

    # ---- TUPLES GENERATION FROM FK CONSTRAINTS ----

    def generate_fk_attr_vals(self, fed_tuples):
        o_rel_tuples_fk = {}  # to feed as {Relation: [{attr1: val1,..}, {attr1: val1,..}], Relation2: [FK attr vals], }
        for ind_attr_fk, rel_mapping in self.get_ind_fixed_attr_in_fk().items():
            rel, attr_names_mapping = rel_mapping
            for tup in fed_tuples:
                # keep subset of generated tuple values considering only attributes in FK referencing rel
                tup_fk_val = itemgetter(*ind_attr_fk)(tup)
                tup_fk_attr = itemgetter(*ind_attr_fk)(self.attribute_fix)
                if not isinstance(tup_fk_attr, tuple):
                    #  itemgetter does not return tuple if response is a standalone element
                    tup_fk_val = (tup_fk_val,)
                    tup_fk_attr = (tup_fk_attr,)
                dict_attr_val = {}
                for ind in range(len(ind_attr_fk)):
                    # rebuilding unordered dict {attr1: val1, attr2: val2, ..} where attrN belongs to FK to rel
                    name_attr_in_o_rel = attr_names_mapping[tup_fk_attr[ind]]
                    attr, val = name_attr_in_o_rel, tup_fk_val[ind]
                    dict_attr_val[attr] = val
                if o_rel_tuples_fk.get(rel) is None:
                    o_rel_tuples_fk[rel] = [dict_attr_val]
                else:
                    o_rel_tuples_fk[rel].append(dict_attr_val)
        return o_rel_tuples_fk

    # ---- UTILITIES ----

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

    # ---- GETTERS ----

    def get_tuples_indexes(self, nbr, selector=None, rdm_selection=False):
        if nbr <= self.get_size():
            enough = (True, 0)
        else:
            enough = (False, nbr - self.get_size())
            nbr = self.get_size()
        poss_indexes = list(range(self.get_size()))
        if rdm_selection:
            random.shuffle(poss_indexes)
        if selector is None:
            slcted = poss_indexes[:nbr]
        else:
            slcted = []
            for ind in poss_indexes:
                if len(slcted) >= nbr:
                    return slcted
                ind_to_check = poss_indexes[ind]
                if selector(self[ind_to_check]):
                    slcted.append(ind_to_check)
        if not enough[0]:  # need to repick additional indexes in the selected ones
            times_whole_slcted, remaining = divmod(enough[1], len(slcted))
            slcted.extend(slcted*times_whole_slcted + slcted[:remaining])
        return slcted

    def get_tuples_indexes2(self, nbr, selector=None, rdm_selection=False):
        nbr = min(nbr, self.get_size())
        poss_indexes = list(range(self.get_size()))
        if rdm_selection:
            random.shuffle(poss_indexes)
        if selector is None:
            return poss_indexes[:nbr]
        slcted = []
        for ind in poss_indexes:
            if len(slcted) >= nbr:
                return slcted
            ind_to_check = poss_indexes[ind]
            if selector(self[ind_to_check]):
                slcted.append(ind_to_check)
        return slcted

    def get_tuples(self, nbr, only_values=True, selector=lambda tuple_info: True, rdm=False, in_subset=None):
        result = []
        indexes = range(self.get_size()) if in_subset is None else in_subset.copy()
        if rdm:
            random.shuffle(indexes)
        for i in range(min(nbr, len(indexes))):
            test_tuple = self.tuples[indexes[i]]
            if selector(test_tuple):
                result.append(test_tuple[0] if only_values else test_tuple)
        return result

    def get_size(self):
        return len(self.tuples)

    def get_rel_model(self):
        return self.rel_model

    def get_name(self):
        return self.rel_model.name

    def get_fixed_attributes(self):
        return self.attribute_fix

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

    def repr_n_tuples(self, tuples, n=10):
        max_lens = []
        sel_tuples = tuples[:n]
        attributes = [f"[{attr}]" if self.rel_model.pk_contains(attr) else attr for attr in self.attribute_fix]
        attributes = [f"<{attr}>" if self.rel_model.is_in_fks(attr) else attr for attr in attributes]
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

    def __getitem__(self, item):
        return self.tuples[item]


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
#    print(inst.generate_new_tuple(given_attr_values={"pk": '1'}))
#    print(inst.get_tuples_indexes(10, selector=lambda t: t[0][0] > "1", rdm_selection=True))

    # print(inst.degenerate_tuples_at_inds([0, 1]))
    inst.degenerate_and_feed_tuples_at_inds([0,1])
    print(inst)
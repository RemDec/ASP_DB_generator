from operator import add, sub
from functools import reduce
import random


class SchemaError(ValueError):

    def __init__(self, msg, schema):
        super().__init__(msg)
        self.schema = schema


class RelationInstance:

    def __init__(self, rel_model, attribute_fix, init_tuples=None):
        self.rel_model = rel_model
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

    def get_size(self):
        return len(self.tuples)

    def repr_n_tuples(self, tuples, n=10):
        max_lens = []
        sel_tuples = tuples[:n]
        for col, attr_name in enumerate(self.attribute_fix):
            col_attr = [tup[0][col] for tup in sel_tuples]
            max_width_tup_val = reduce(lambda c, s: max(c, len(s)), col_attr, -1)
            width = max(len(attr_name), max_width_tup_val)
            max_lens.append(width)
        s = f"{self.rel_model.name} "
        shifting = len(s)
        s += '|'
        info_header = " C D "
        for i, attr_name in enumerate(self.attribute_fix):
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

    def __str__(self):
        return self.repr_n_tuples(self.tuples, self.get_size())


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

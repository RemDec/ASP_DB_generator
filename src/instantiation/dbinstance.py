

class DBInstance:

    def __init__(self, rels_inst_params, respect_fk=True):
        self.rels_inst_params = rels_inst_params
        self.respect_fk = respect_fk
        self.rel_insts = {}
        self.generate_instances()

    def generate_instances(self):
        fk_tuples = {}
        rel_insts = {}
        for rel, param in self.rels_inst_params:
            # multiple formats allowed for param -> normalize to
            # (param_generation, attr_sequence_order, respect_fk_constraint) as taken by Relation.generate_instance
            if isinstance(param, int):
                param = (param,)
            if len(param) == 1:  # nbr of tuples to generate for rel
                param = (param[0], None, self.respect_fk)
            elif len(param) == 2:  # nbr tuples + attr_seq_order
                param = (param[0], param[1], self.respect_fk)
            # if len(param) == 3, respect_fk is given explicitly for this relation
            rel_inst, gen_fk_tuples = rel.generate_instance(param[0], param[1], param[2])
            rel_insts[rel.name] = rel_inst
            for o_rel, tuples in gen_fk_tuples.items():
                already_generated = fk_tuples.get(o_rel.name, False)
                if not already_generated:
                    fk_tuples[o_rel.name] = tuples
                else:
                    fk_tuples[o_rel.name].extend(tuples)

        self.rel_insts = rel_insts
        print(fk_tuples)
        while fk_tuples:
            rel_name, tuples = fk_tuples.popitem()
            rel_inst = self.rel_insts.get(rel_name, None)
            if rel_inst:
                rel_inst.generate_and_feed_tuples(tuples, from_constraint=True)
        return rel_insts, fk_tuples

    def __str__(self):
        s = f"DBInstance with {len(self.rel_insts)} relation instances\n"
        for name, rel_inst in self.rel_insts.items():
            s += str(rel_inst) + '\n'
        return s


if __name__ == "__main__":
    from src.model.attribute import AttributeInfo, AttributeTypes
    from src.model.relation import Relation

    def compose_attr3(other_attr_value):
        return other_attr_value.get("attr1", "UNK") + '-' + other_attr_value.get("attr2", "UNK")

    pk_int = AttributeInfo("impk", attr_type=AttributeTypes.incr_int)
    attr1 = AttributeInfo("attr1", desc="random integer")
    attr2 = AttributeInfo("attr2", attr_type=AttributeTypes.str)
    fk_str = AttributeInfo("imfk", attr_type=AttributeTypes.str, gen_order=2,
                           get_generator_fun=lambda _: compose_attr3,
                           desc="composed from attr1 attr2")

    SRel = Relation("SRel", pk="pkattr",
                    attributes={"pkattr": pk_int,
                                "attr1": attr1,
                                "attr2": attr2,
                                "attr3": fk_str})

    pk_fk = AttributeInfo("attr3", attr_type='str')
    attr4 = AttributeInfo("attr4", attr_type=AttributeTypes.incr_str)
    RRel = Relation("RRel", pk="attr3", attributes=[pk_fk, attr4])
    SRel.add_fk_constraint({"attr3": RRel})

    db = DBInstance([(SRel, 4), (RRel, 0)])
    print(db)
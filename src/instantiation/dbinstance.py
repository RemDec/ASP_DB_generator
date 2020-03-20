

class DBInstance:

    def __init__(self, rels_inst_params, respect_fk=True, generate=True):
        self.rels_inst_params = []
        self.respect_fk = respect_fk
        self.rel_insts = {}
        self.treat_instantiation_params(rels_inst_params)
        if generate:
            self.generate_instances()

    def treat_instantiation_params(self, rels_inst_params):
        # rels_inst_params list of couples (Relation, param) where param parametrizes instantiation from Relation
        for rel, param in rels_inst_params:
            # multiple formats allowed for param -> normalize to
            # (param_generation, attr_sequence_order, respect_fk_constraint) as taken by Relation.generate_instance
            if isinstance(param, int):
                param = (param,)
            if len(param) == 1:  # nbr of tuples to generate for rel
                param = (param[0], None, self.respect_fk)
            elif len(param) == 2:  # nbr tuples + attr_seq_order
                param = (param[0], param[1], self.respect_fk)
            # if len(param) == 3, respect_fk is given explicitly for this relation
            self.rels_inst_params.append((rel, param))

    def generate_tuples_from_fks(self, curr_fk_tuples):
        # curr_fk_tuple as {relname : [{attr1: val1,..}, {attr1: val1,..}], relname2: [...]}
        # where each {attr: val, attr2: val2} are partially valued attribute of a FK tuple referencing relname
        while curr_fk_tuples:
            rel_name, tuples = curr_fk_tuples.popitem()
            rel_inst = self.rel_insts.get(rel_name, None)
            if rel_inst:
                # generate full tuple for rel from partial attribute values from FK constraint
                _, fk_generated = rel_inst.generate_and_feed_tuples(tuples, from_constraint=True)
                # if rel had also FK to another rel2, it also generates partial tuple to complete for rel2
                for o_rel, o_tuples in fk_generated.items():
                    if curr_fk_tuples.get(o_rel.name) is None:
                        curr_fk_tuples[o_rel.name] = o_tuples
                    else:
                        curr_fk_tuples[o_rel.name].extend(o_tuples)

    def generate_instances(self):
        fk_tuples = {}
        rel_insts = {}  # {relname: RelationInstance} where RelationInstance is the one generated from params
        # generate all regular tuples from instantiation parameters given for each relation
        for rel, param in self.rels_inst_params:
            rel_inst, gen_fk_tuples = rel.generate_instance(param[0], param[1], param[2])
            rel_insts[rel.name] = rel_inst
            # keep all partially generated tuples originated from FK constraints in fk_tuples with entries
            # like relname : [{attr1: val1,..}, {attr1: val1,..}] where {attr1: val1} is a partially generated
            # tuple for relation relname (attr1 was in a FK referencing relname that has attr1 as PK)
            for o_rel, tuples in gen_fk_tuples.items():
                already_generated = fk_tuples.get(o_rel.name, False)
                if not already_generated:
                    fk_tuples[o_rel.name] = tuples
                else:
                    fk_tuples[o_rel.name].extend(tuples)
        self.rel_insts = rel_insts
        self.generate_tuples_from_fks(fk_tuples)
        return rel_insts

    def repr_ASP(self):
        s = ""
        for relinst in self.rel_insts.values():
            s += relinst.repr_ASP()
        return s

    def __str__(self):
        s = f"DBInstance with {len(self.rel_insts)} relation instances, generated from parameters :\n"
        for rel, (param_gen, attr_sequence_order, respect_fk_constraint) in self.rels_inst_params:
            attr_sequence_order = "ALL" if attr_sequence_order is None else ','.join(attr_sequence_order)
            s += f">Relation {rel.name} : kept attributes={attr_sequence_order} |" \
                 f" respect FK={respect_fk_constraint} | params for generation={param_gen}\n"
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

    TRel = Relation("TRel", pk="attr4", attributes=attr4.__copy__())
    RRel.add_fk_constraint({"attr4": TRel})

    db = DBInstance([(SRel, 4), (RRel, 0), (TRel, 0)])
    print(db)
    #print(db.repr_ASP())
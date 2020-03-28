from src.utils.utilfunctions import fill_tuple_dflt_vals
from src.model.relation import Relation


class DBInstance:

    def __init__(self, rels_inst_params, respect_fk=True, generate=True):
        self.rels_inst_params = []
        self.respect_fk = respect_fk
        self.rel_insts = {}  # to fill as {relname: RelInstance} where RelInstance will be the one generated from params
        self.treat_instantiation_params(rels_inst_params)
        if generate:
            self.generate_instances()

    # ---- RELATION INSTANCES GENERATION ----

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
                already_generated = fk_tuples.get(o_rel.name, None)
                if not already_generated:
                    fk_tuples[o_rel.name] = tuples
                else:
                    fk_tuples[o_rel.name].extend(tuples)
        self.rel_insts = rel_insts
        self.generate_tuples_from_fks(fk_tuples)
        return rel_insts

    # ---- RELATION INSTANCES DEGENERATION ----

    def degenerate_inst(self, rel, nbr, fixed_attr=None, selector=None, rdm_selection=False,
                        respect_fk_constraint=True):
        rel_inst = self.get_rel_inst(rel)
        tuples_indexes = rel_inst.get_tuples_indexes(nbr, selector=selector, rdm_selection=rdm_selection)
        # return degenerated_tuples_list, o_rel_fk_attr_values_dict
        return rel_inst.degenare_and_feed_tuples_at_inds(tuples_indexes, fixed_attr=fixed_attr,
                                                         respect_fk_constraint=respect_fk_constraint)

    def degenerate_insts(self, insts_deg_params):
        insts_deg_params = self.treat_degenaration_params(insts_deg_params)
        fk_tuples = {}
        for rel_inst, deg_params in insts_deg_params.items():
            nbr, rdm_slct, selector_fct, fixed_attrs = deg_params
            tuples_indexes = rel_inst.get_tuples_indexes(nbr, selector=selector_fct, rdm_selection=rdm_slct)
            _, deg_fk_tuples = rel_inst.degenerate_and_feed_tuples_at_inds(tuples_indexes, fixed_attrs=fixed_attrs,
                                                                           respect_fk_constraints=self.respect_fk)
            self.fill_fk_tuples_per_rel(fk_tuples, deg_fk_tuples)
        self.generate_tuples_from_fks(fk_tuples)

    # ---- UTILITIES ----

    def treat_instantiation_params(self, rels_inst_params):
        for rel, global_params_for_inst in rels_inst_params.items():
            param = global_params_for_inst
            if isinstance(param, int) or isinstance(param, list) or isinstance(param, dict):
                param = (param, None, self.respect_fk)
            if isinstance(param, tuple):
                if len(param) == 1:
                    param = (param, None, self.respect_fk)
                elif len(param) == 2:
                    param = (param[0], param[1], self.respect_fk)
                else:
                    param = (param[0], param[1], param[2])
                # param is now (inst_params, seq_attr, respect_FK) where inst_params is a list of elements of 3 forms :
                #  1. integer nbr of tuples to generate
                #  2. tuple (nbr, {attr: val}) to generate nbr tuple considering value val for attribute attr
                #  3. list [tuples of 2.] to generate multiple tuples considering different given val for some attr
                # inst_params will be passed as-is to function Relation.generate_instance at generation time
                self.rels_inst_params.append((rel, param))

    def treat_degenaration_params(self, rels_deg_params):
        treated_params = {}
        for rel, degeneration_params in rels_deg_params.items():
            rel_inst = self.get_rel_inst(rel)
            param = degeneration_params
            if isinstance(param, int):
                param = (param,)
            param = fill_tuple_dflt_vals(param, (0, False, None, None))
            # param is now as (nbr_to_deg, fixed_attrs, selector_fct, rdm_select)
            treated_params[rel_inst] = param
        return treated_params

    def fill_fk_tuples_per_rel(self, curr_fk_tuples_per_rel, new_generated_fk_tuples):
        for o_rel, tuples in new_generated_fk_tuples.items():
            already_generated = curr_fk_tuples_per_rel.get(o_rel.name, None)
            if not already_generated:
                curr_fk_tuples_per_rel[o_rel.name] = tuples
            else:
                curr_fk_tuples_per_rel[o_rel.name].extend(tuples)

    # ---- GETTERS ----

    def get_rel_inst(self, rel):
        if isinstance(rel, str):
            return self.rel_insts.get(rel)
        elif isinstance(rel, Relation):
            return self.rel_insts.get(rel.name)

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
        s += '\n'
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

    db = DBInstance({SRel: 10, RRel: 0, TRel: 0})
    print(db)
    # print(db.repr_ASP())

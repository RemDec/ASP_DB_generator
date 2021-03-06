from operator import itemgetter
from src.model.attribute import AttributeInfo
from src.instantiation.relinstance import RelationInstance
from src.utils.utilfunctions import single_to_tuple, get_indexes, normalize_gen_param, fill_tuple_dflt_vals


class KeyMaterialError(ValueError):

    def __init__(self, msg, relation):
        super().__init__(msg)
        self.relation = relation


class Relation:

    def __init__(self, name, attributes=None, pk=None):
        self.name = name
        self.attributes = {}
        self.treat_attributes(attributes)
        self.pk = []
        self.define_pk(pk)
        self.fks = {}

    # ---- SCHEMA ATTR MANIPULATIONS ----

    def add_attribute(self, attrib_info, pk=False, name=None):
        name_in_rel = attrib_info.name if name is None else name
        self.attributes[name_in_rel] = attrib_info
        if pk:
            if not(name_in_rel in self.pk):
                self.pk.append(name_in_rel)

    def treat_attributes(self, attributes):
        if isinstance(attributes, list):
            for attr in attributes:
                self.add_attribute(attr)
        elif isinstance(attributes, dict):
            for attr_name, attr_info in attributes.items():
                self.add_attribute(attr_info, name=attr_name)
        elif isinstance(attributes, AttributeInfo):
            self.add_attribute(attributes)

    def add_fk_constraint(self, map_to_others_rel):
        for attr_names, foreign_rel_mapping in map_to_others_rel.items():
            attr_names = single_to_tuple(attr_names)
            name_mapping = {}
            foreign_rel = foreign_rel_mapping
            if isinstance(foreign_rel_mapping, Relation):
                for attr in attr_names:
                    name_mapping[attr] = attr
            elif len(foreign_rel_mapping) == 2:
                foreign_rel = foreign_rel_mapping[0]
                renamed_attrs = foreign_rel_mapping[1]
                for attr in attr_names:
                    if attr in renamed_attrs:
                        name_mapping[attr] = renamed_attrs[attr]
                    else:
                        name_mapping[attr] = attr
            foreign_rel_mapping = (foreign_rel, name_mapping)
            if not foreign_rel.pk_contains(name_mapping.values()):
                err = f"Given FK for {self.name} wrongly references PK in relation {foreign_rel.name}"
                raise KeyMaterialError(err, foreign_rel)
            self.fks[attr_names] = foreign_rel_mapping

    def define_pk(self, pk):
        if isinstance(pk, str):
            self.pk = [pk]
        elif isinstance(pk, AttributeInfo):
            self.pk = [pk.name]
        elif isinstance(pk, list):
            self.pk = [attr.name if isinstance(attr, AttributeInfo) else attr for attr in pk]
        else:
            self.pk = []
        self.verify_pk()

    def verify_pk(self):
        if self.pk is None:
            raise KeyMaterialError(f"Undefined PK for relation {self.name}", self)
        for attr in self.pk:
            if not(attr in self.attributes):
                raise KeyMaterialError(f"Inconsistent PK : attribute {attr} not in relation {self.name}", self)
        return True

    # ---- TUPLES/INSTANCES GENERATION FROM SCHEMA ----

    def reset_attr_generators(self):
        for attr_infos in self.attributes.values():
            attr_infos.reset_generator()

    def fix_tuple_values(self, valued_attributes, attr_sequence_order=None, keep_attr_name=True):
        # from generated tuple values, fix them following a given sequence of attributes name, return corresp. values
        tup = []
        if attr_sequence_order is None:
            attr_sequence_order = self.get_dflt_attr_sequence()
        for attr_name in attr_sequence_order:
            if valued_attributes.get(attr_name, False):
                if keep_attr_name:
                    tup.append((attr_name, valued_attributes[attr_name]))
                else:
                    tup.append(valued_attributes[attr_name])
            else:
                err = f"Queried attribute {attr_name} wasn't generated in the tuple for relation {self.name}"
                raise KeyMaterialError(err, self)
        return tuple(tup)

    def generate_tuple_missing_val(self, attr_info_missing, already_known_val):
        for attr_info, attr_name in attr_info_missing:  # assuming it's ordered following generation order
            # generate value for attr considering all previous value already generated for others (with <= order)
            already_known_val[attr_name] = attr_info.get_generated_value(already_known_val)  # side-effect on dict

    def generate_tuple(self, given_attr_values, attr_sequence_order=None, keep_attr_name=True):
        attr_pk_not_valued, attr_not_valued = [], []
        for attr in self.attributes:
            if not(attr in given_attr_values):
                if self.pk_contains(attr):
                    attr_pk_not_valued.append(attr)
                else:
                    attr_not_valued.append(attr)
        given_attr_values = given_attr_values.copy()
        # generate first missing values for attr in PK, ordering generation with order value defined in each attr_info
        self.generate_tuple_missing_val(self.get_attr_infos(attr_pk_not_valued), given_attr_values)
        # generate second others attr, considering generated value for PK (side-effect on given_attr_values)
        self.generate_tuple_missing_val(self.get_attr_infos(attr_not_valued), given_attr_values)
        # fix values of generated tuple in sequence order given, return it as a tuple ((attr1, val1), (attr2, val2),...)
        return self.fix_tuple_values(given_attr_values, attr_sequence_order, keep_attr_name)

    def generate_instance(self, param_generation, attr_sequence_order=None, respect_fk_constraint=True, respect_pk=True):
        param_generation = normalize_gen_param(param_generation)
        if attr_sequence_order is None:
            attr_sequence_order = self.get_dflt_attr_sequence()
        tuples_with_given_vals = []
        for nbr_tuples, given_attr_vals in param_generation:
            # from entries (nbr, {attr1: val1, attr2, val2}) to {attr1: val1, attr2, val2} nbr times in a list
            tuples_with_given_vals.extend([given_attr_vals]*nbr_tuples)
        rel_inst = RelationInstance(self.__copy__(), attr_sequence_order)
        _, o_rel_tuples_fk = rel_inst.generate_and_feed_tuples(tuples_with_given_vals, respect_pk=respect_pk,
                                                               respect_fk_constraint=respect_fk_constraint)
        return rel_inst, o_rel_tuples_fk

    # ---- UTILITIES ----

    def is_in_fks(self, attr):
        if isinstance(attr, AttributeInfo):
            attr = attr.name
        for fk in self.fks:
            if attr in fk:
                return True
        return False

    def pk_contains(self, attrs):
        attrs = single_to_tuple(attrs)
        for attr in attrs:
            if not(attr in self.pk):
                return False
        return True

    def constitute_fk(self, attrs):
        attrs = single_to_tuple(attrs)
        return self.fks.get(attrs)

    # ---- GETTERS ----

    def get_belongs_fk(self, attrs):
        attrs = single_to_tuple(attrs)
        found_fk = []
        for fk in self.fks:
            ok = True
            for attr in attrs:
                if not(attr in fk):
                    ok = False
                    break
            if ok:
                found_fk.append(fk)
        return found_fk

    def get_pk_attr(self):
        return self.pk.copy()

    def get_nonpk_attr(self):
        return [attr for attr in self.attributes if not self.pk_contains(attr)]

    def get_fks_attr(self):
        return self.fks.keys()

    def get_all_attr(self, ordered_by_gen=True):
        if not ordered_by_gen:
            in_pk, others = [], []
            for attr in self.attributes:
                if self.pk_contains(attr):
                    in_pk.append(attr)
                else:
                    others.append(attr)
        else:
            non_pk_attr = self.get_nonpk_attr()
            in_pk = map(itemgetter(1), self.get_attr_infos(self.pk))
            others = map(itemgetter(1), self.get_attr_infos(non_pk_attr))
        return list(in_pk), list(others)

    def get_dflt_attr_sequence(self):
        pk_attr, others_attr = self.get_all_attr()
        return pk_attr + others_attr

    def get_attr_infos(self, attributes, sort_them=True):
        # retrieve attributes info objects and may sort these using order value to follow for tuple generation
        attributes = single_to_tuple(attributes)
        info = []
        for attr in attributes:
            if attr in self.attributes:
                info.append((self.attributes[attr], attr))  # formatted as (AttributeInfo, attr_name_in_rel)
        return sorted(info) if sort_them else info

    def __copy__(self):
        reset_attrs = {}
        for attr_name, attr in self.attributes.items():
            reset_attrs[attr_name] = attr.__copy__()
        copy_rel = Relation(self.name, attributes=reset_attrs, pk=self.pk.copy())
        copy_rel.add_fk_constraint(self.fks.copy())  # CARE NO DEEP COPY OF RELATIONS REFERENCED BY FKs !!!
        return copy_rel

    def __str__(self):
        pk_attr, o_attr = self.get_all_attr()
        s = f"Relation {self.name}"
        shifting = len(s)
        s += "| vvv PK vvv\n"

        def disp_attributes_info(attributes):
            s = ""
            for attr in attributes:
                attr_info = self.attributes[attr]
                s += f"{' '*shifting}| {attr} : {attr_info}\n"
                in_fk = self.get_belongs_fk(attr)
                if in_fk:
                    s = s[:-1]
                    for fk_key in in_fk:
                        o_rel, mapping_names = self.fks.get(fk_key)
                        map_name = ""
                        if mapping_names[attr] != attr:
                            map_name = f"({attr}->{mapping_names[attr]})"
                        s += f" - FK referencing {o_rel.name} {map_name}"
                    s += "\n"
            return s
        s += disp_attributes_info(pk_attr)
        s += ' '*shifting + "| vvv OTHERS vvv\n"
        s += disp_attributes_info(o_attr)
        return s


if __name__ == "__main__":
    from src.model.attribute import AttributeInfo, AttributeTypes

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

    RRel = Relation("RRel", pk="attr3", attributes={"attr3": AttributeInfo("attr3", attr_type=AttributeTypes.str)})
    SRel.add_fk_constraint({"attr3": (RRel, {"attr3": "pk_in_o_rel"})})

    print(SRel, RRel, sep='\n')
    print("generating tuples from SRel ...")
    for i in range(5):
        print(SRel.generate_tuple({}))
    print("generate and project tuple to a shortened attributes sequence")
    print(SRel.generate_tuple(given_attr_values={"attr1": "first", "attr2": "second"},
                              attr_sequence_order=["pkattr", "attr3"]))

    print("generate an instance from SRel ...")
    inst1, fk_gen = SRel.generate_instance(10)
    print(inst1)
    print("FK constraints returned tuple to add to respect properties", fk_gen, "\n\n")

    inst2, fk_gen2 = SRel.generate_instance([(5, {}), (5, {"attr2": "fixed"})], attr_sequence_order=["attr3", "pkattr"])
    print("SECOND generated instance from SREL should restart PK increment (new generators)\n", inst2)
    print("FK constraints returned tuple to add to respect properties", fk_gen2)
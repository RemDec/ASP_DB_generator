from operator import itemgetter


class KeyMaterialError(ValueError):

    def __init__(self, msg, relation):
        super().__init__(msg)
        self.relation = relation


class Relation:

    def __init__(self, name, attributes=None, pk=None):
        self.name = name
        self.attributes = {} if attributes is None else attributes
        self.pk = []
        self.define_pk(pk)
        self.fks = {}

    def add_attribute(self, attrib_info, pk=False, name=None):
        name_in_rel = attrib_info.name if name is None else name
        self.attributes[name_in_rel] = attrib_info
        if pk:
            if not(name_in_rel in self.pk):
                self.pk.append(name_in_rel)

    def add_fk_constraint(self, map_to_others_rel):
        for attr_name, foreign_rel in map_to_others_rel.items():
            if not foreign_rel.pk_contains(attr_name):
                err = f"Given FK for {self.name} wrongly references PK in relation {foreign_rel.name}"
                raise KeyMaterialError(err, foreign_rel)
            self.fks[attr_name] = foreign_rel

    def define_pk(self, pk):
        if isinstance(pk, str):
            self.pk = [pk]
        elif isinstance(pk, list):
            self.pk = pk
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

    def pk_contains(self, attr):
        return attr in self.pk

    def get_pk_attr(self):
        return self.pk.copy()

    def get_nonpk_attr(self):
        return [attr for attr in self.attributes if not self.pk_contains(attr)]

    def get_fk_attr(self):
        return self.attributes.keys()

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

    def get_attr_infos(self, attributes, sort_them=True):
        # retrieve attributes info objects and may sort these using order value to follow for tuple generation
        info = []
        for attr in attributes:
            if attr in self.attributes:
                info.append((self.attributes[attr], attr))
        return sorted(info) if sort_them else info

    def generate_tuple_missing_val(self, attr_info_missing, already_known_val):
        for attr_info, attr_name in attr_info_missing:  # supposing it's ordered following generation order
            # generate value for attr considering all previous value already generated for others (with <= order)
            already_known_val[attr_name] = attr_info.get_generated_value(already_known_val)  # side-effect on dict

    def fix_tuple_values(self, valued_attributes, attr_sequence_order=None, keep_attr_name=True):
        # from generated tuple values, fix them following a given sequence of attributes name, return corresp. values
        tup = []
        if attr_sequence_order is None:
            pk_attr, others_attr = self.get_all_attr()
            attr_sequence_order = pk_attr + others_attr
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

    def generate_tuple(self, given_attr_values, attr_sequence_order=None, keep_attr_name=True):
        attr_pk_not_valued, attr_not_valued = [], []
        for attr in self.attributes:
            if not(attr in given_attr_values):
                if self.pk_contains(attr):
                    attr_pk_not_valued.append(attr)
                else:
                    attr_not_valued.append(attr)
        # generate first missing values for attr in PK, ordering generation with order value defined in each attr_info
        self.generate_tuple_missing_val(self.get_attr_infos(attr_pk_not_valued), given_attr_values)
        # generate second others attr, considering generated value for PK (side-effect on given_attr_values)
        self.generate_tuple_missing_val(self.get_attr_infos(attr_not_valued), given_attr_values)
        # fix values of generated tuple in sequence order given, return it as a tuple ((attr1, val1), (attr2, val2),...)
        return self.fix_tuple_values(given_attr_values, attr_sequence_order, keep_attr_name)

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
                if attr in self.fks:
                    s = s[:-1]
                    s += f" - FK for {self.fks[attr].name}\n"
            return s
        s += disp_attributes_info(pk_attr)
        s += ' '*shifting + "| vvv OTHERS vvv\n"
        s += disp_attributes_info(o_attr)
        return s


if __name__ == "__main__":
    from src.model.attribute import AttributeInfo, AttributeTypes

    def compose_attr3(other_attr_value):
        return other_attr_value.get("attr1", "UNK") + '-' + other_attr_value.get("attr2", "UNK")

    SRel = Relation("SRel", pk="pkattr",
                    attributes={"pkattr": AttributeInfo("impk", attr_type=AttributeTypes.incr_int),
                                "attr1": AttributeInfo("attr1", desc="random integer"),
                                "attr2": AttributeInfo("attr2", attr_type=AttributeTypes.str),
                                "attr3": AttributeInfo("imfk", attr_type=AttributeTypes.str,
                                                       gen_order=2, value_generator=compose_attr3,
                                                       desc="composed from attr1 attr2")},
                    )

    RRel = Relation("RRel", pk="attr3", attributes={"attr3": AttributeInfo("attr3", attr_type=AttributeTypes.str)})
    SRel.add_fk_constraint({"attr3": RRel})

    print(SRel, RRel, sep='\n')

    for i in range(5):
        print(SRel.generate_tuple({}))

    print(SRel.generate_tuple(given_attr_values={"attr1": "first", "attr2": "second"},
                              attr_sequence_order=["pkattr", "attr3"]))

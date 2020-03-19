import src.model.generators as generators
import enum
import copy


class AttributeTypes(enum.Enum):
    int = "INTEGER"
    str = "STRING"
    date = "DATE"
    incr_int = "INTEGER_INCR"
    incr_str = "STRING_INCR"


def dflt_gen_for_type(attr_type):
    if attr_type == AttributeTypes.int:
        return generators.get_generator_rdm_int()
    if attr_type == AttributeTypes.incr_int:
        return generators.get_generator_increment_int()
    if attr_type == AttributeTypes.str:
        return generators.get_generator_rdm_str()
    if attr_type == AttributeTypes.incr_str:
        return generators.get_generator_increment_str()


class AttributeInfo:

    def __init__(self, name, attr_type=AttributeTypes.int, get_generator_fun=dflt_gen_for_type, gen_order=1, desc=""):
        # get_generator_fun(attr_type) should return either a fun such as fun(o_attr_values) returns a value
        # either a fun such as fun() returns an iterator generator supporting next(generator)
        self.name = name
        self.attr_type = AttributeTypes[attr_type] if isinstance(attr_type, str) else attr_type
        self.get_generator_fun = get_generator_fun  # useful to reset getting a fresh new python generator type object
        self.generator = get_generator_fun(self.attr_type)
        self.order = max(gen_order, 0)
        self.desc = desc

    def reset_generator(self):
        self.generator = self.get_generator_fun(self.attr_type)

    def get_generated_value(self, other_attr_values=None):
        other_attr_values = {} if other_attr_values is None else other_attr_values
        if other_attr_values.get(self.name) is not None:  # already generated value in ones given
            return other_attr_values[self.name]
        try:
            return str(next(self.generator))  # In case generator is actually a generator/iterable
        except TypeError:
            return str(self.generator(other_attr_values))

    def get_gen_order(self):
        return self.order

    def get_attr_type_value(self):
        return self.attr_type.value

    def __le__(self, other):
        return self.order <= other.get_gen_order()

    def __lt__(self, other):
        return self.order < other.get_gen_order()

    def __ge__(self, other):
        return self.order >= other.get_gen_order()

    def __copy__(self):
        return AttributeInfo(self.name, self.attr_type, self.get_generator_fun, self.order, self.desc)

    def __str__(self):
        s = f"{self.name} [{self.order}] ({self.attr_type.value})"
        if self.desc:
            s += f" desc : {self.desc}"
        return s


if __name__ == "__main__":
    attr1 = AttributeInfo("attr1")
    attr2 = AttributeInfo("attr2", attr_type=AttributeTypes.incr_int, gen_order=2)
    attr3 = AttributeInfo("attr3", attr_type=AttributeTypes.str, gen_order=-1)
    attr4 = AttributeInfo("attr4", attr_type=AttributeTypes.incr_str)

    print(attr1, attr2, attr3, attr4,
          f"order attr1 < attr2 : {attr1 < attr2}",
          f"order attr2 < attr3 : {attr2 < attr3}", sep='\n')
    print("Generating 5 values for each..")
    for attr in [attr1, attr2, attr3, attr4]:
        print(f"{attr.name} :", ', '.join(attr.get_generated_value({}) for _ in range(5)))

    print("Reset generator attr2 (INCR_INT, should restart to val 1)..")
    attr2.reset_generator()
    print(" +-> new vals generated after reset :", [attr2.get_generated_value() for _ in range(5)])
    attr_copy = attr2.__copy__()
    print("Copying attr2, generating 5 values from copy should not impact attr2 generation")
    print(" +-> 5 values from attr2 copy :", [attr_copy.get_generated_value() for _ in range(5)])
    print(" +-> next val for attr2 :", attr2.get_generated_value())


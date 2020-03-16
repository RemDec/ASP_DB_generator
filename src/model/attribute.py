import src.model.generators as generators
import enum


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

    def __init__(self, name, attr_type=AttributeTypes.int, value_generator=None, gen_order=1, desc=""):
        self.name = name
        self.attr_type = attr_type
        self.generator = dflt_gen_for_type(attr_type) if value_generator is None else value_generator
        self.order = max(gen_order, 0)
        self.desc = desc

    def get_generated_value(self, other_attr_values):
        if other_attr_values.get(self.name) is not None:
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
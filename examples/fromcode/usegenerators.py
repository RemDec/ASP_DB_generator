from src.model.attribute import AttributeInfo
from src.model.generators import *

if __name__ == "__main__":
    attr_rdm_int = AttributeInfo("rmd_int", "int", get_generator_fun=get_generator_rdm_int(10, 15))
    print(attr_rdm_int, "function to get generator=", attr_rdm_int.get_generator_fun,
          " returned generator", attr_rdm_int.generator)
    print([attr_rdm_int.get_generated_value({}) for _ in range(10)])
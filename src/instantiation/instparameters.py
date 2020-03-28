from src.utils.utilfunctions import normalize_gen_param


class TableParameters:

    def __init__(self, nbr_tuples, given_attr=None, proj_attrs=None, respect_fk=True,
                 part_deg=0, rdm_slct=False, selector=None, fixed_attr_deg=None):
        self.nbr_tuples = nbr_tuples
        self.given_attr = [] if given_attr is None else given_attr
        self.proj_attrs = proj_attrs
        self.respect_fk = respect_fk
        self.part_deg = part_deg
        self.rdm_slct = rdm_slct
        self.selector = selector
        self.fixed_attr_deg = fixed_attr_deg

    def get_instantiation_params(self):
        normalized = normalize_gen_param(self.given_attr)
        curr_nbr = 0
        tuple_params = []
        for nbr_to_gen, given_attr_vals in normalized:
            curr_nbr += nbr_to_gen
            if curr_nbr > self.nbr_tuples:  # cannot generate more, ignore remaining
                break
            tuple_params.append((nbr_to_gen, given_attr_vals))
        nbr_without_given_attr = self.nbr_tuples - curr_nbr
        if nbr_without_given_attr > 0:
            tuple_params.insert(0, nbr_without_given_attr)
        return tuple_params, self.proj_attrs, self.respect_fk

    def get_degeneration_params(self):
        return self.get_nbr_tuples_to_deg(), self.rdm_slct, self.selector, self.fixed_attr_deg

    def get_nbr_tuples_to_deg(self):
        return (self.nbr_tuples * self.part_deg) // 100

    def __str__(self):
        nbr = f"{self.nbr_tuples} tuples"
        if self.proj_attrs is None:
            proj_str = "using all attributes"
        else:
            proj_str = "projecting on attrs " + ','.join(self.proj_attrs)
        resp_fk = "respect FKs at generation " + str(self.respect_fk)
        part_deg = f"{self.part_deg}%"
        rdm = "randomly selected" if self.rdm_slct else "sequentially selected"
        slctor = ("no" if self.selector is None else "") + " selector fct"
        deg_attr = "on " + "PK" if self.fixed_attr_deg is None else ','.join(self.fixed_attr_deg)
        s = f"TableParameter : {nbr} - {proj_str} - {resp_fk} | degenerating {part_deg} - {deg_attr} - {rdm} - {slctor}"
        s += f"\n  +- {len(self.given_attr)} given attribute values : {self.given_attr}\n"
        return s


class GlobalParameters:

    def __init__(self, nbr_tuples, proj_attrs=None, respect_fk=True,
                 part_deg=0, rdm_slct=False, selector=None, fixed_attr_deg=None):
        self.nbr_tuples = nbr_tuples
        self.proj_attrs = proj_attrs
        self.respect_fk = respect_fk
        self.part_deg = part_deg
        self.rdm_slct = rdm_slct
        self.selector = selector
        self.fixed_attr_deg = fixed_attr_deg

    def deduce_table_parameter(self, o_rel_table_params):
        remain_nbr_tuples = self.nbr_tuples
        remain_part_deg = self.part_deg
        nbr_given_table_params = 0
        for _, table_param in o_rel_table_params:
            if table_param is not None:
                nbr_given_table_params += 1
                remain_nbr_tuples -= table_param.nbr_tuples
                remain_part_deg -= table_param.part_deg
        nbr_tables_without_param = len(o_rel_table_params) - nbr_given_table_params
        if nbr_tables_without_param == 0:
            tuples_per_remaining_table = 0  # All relations already have a TableParameter associated 
            part_per_remaining_table = 0
        else:
            tuples_per_remaining_table = max(remain_nbr_tuples, 0) // nbr_tables_without_param
            part_per_remaining_table = max(remain_part_deg, 0) // nbr_tables_without_param
        return TableParameters(tuples_per_remaining_table,
                               given_attr=[], proj_attrs=self.proj_attrs, respect_fk=self.respect_fk,
                               part_deg=part_per_remaining_table, rdm_slct=self.rdm_slct, selector=self.selector,
                               fixed_attr_deg=self.fixed_attr_deg)

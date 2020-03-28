from src.model.relation import Relation
from src.instantiation.instparameters import GlobalParameters
from src.instantiation.dbinstance import DBInstance


class InstantiationProcess:

    def __init__(self, rels_table_params, dflt_param=GlobalParameters(0)):
        self.rel_table_params = self.treat_rels_table_params(rels_table_params)
        self.set_default_rels_table_params(dflt_param)  # to {Relation : TableParameters}, ready to instantiate
        self.db = None

    def instantiate_db(self):
        rels_inst_params = {}
        for rel, table_params in self.rel_table_params.items():
            rels_inst_params[rel] = table_params.get_instantiation_params()
        self.db = DBInstance(rels_inst_params)

    def denegerate_db(self):
        rels_deg_params = {}
        for rel, table_params in self.rel_table_params.items():
            rels_deg_params[rel] = table_params.get_degeneration_params()
        self.db.degenerate_insts(rels_deg_params)

    def set_default_rels_table_params(self, dflt_param):
        if isinstance(dflt_param, GlobalParameters):  # default parameter for each table has to be derived
            dflt_param = dflt_param.deduce_table_parameter(self.rel_table_params.items())
        for rel, param in self.rel_table_params.items():
            if param is None:
                self.rel_table_params[rel] = dflt_param

    def treat_rels_table_params(self, rels_table_params):
        treated = {}
        for relitem in rels_table_params:
            if isinstance(relitem, Relation):
                treated[relitem] = None
            elif isinstance(relitem, tuple) and len(relitem) == 2:  # (Relation, TableParams)
                treated[relitem[0]] = relitem[1]
        return treated

    def __str__(self):
        s = " ### Instantiation process considering following table parameters for each relation :\n"
        for rel, table_param in self.rel_table_params.items():
            s += str(rel) + '\n' + str(table_param) + '\n'
        if self.db is not None:
            s += f" ### The database has been generated :\n\n{self.db}"
        else:
            s += " ### The database has not yet been generated"
        return s

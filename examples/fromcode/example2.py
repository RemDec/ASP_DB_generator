from src.model.relation import Relation
from src.model.attribute import AttributeInfo, AttributeTypes
from src.instantiation.dbinstance import DBInstance
from src.utils.utilfunctions import write_db_inst
from random import randint

if __name__ == "__main__":
    # ---- TABLES ----
    # --- UNIVMEMBERS
    matricule = AttributeInfo("matricule", attr_type=AttributeTypes.incr_int,
                              desc="Registration number in university system")
    persID = AttributeInfo("persid", attr_type=AttributeTypes.str,
                           desc="A personal identifier settable by the member (rdm initially)")
    EXISTING_FACS = ["sciences", "EII", "SHS", "FPSE", "FMM"]

    def get_rdm_fac(_):
        return EXISTING_FACS[randint(0, len(EXISTING_FACS)-1)]
    fac = AttributeInfo("faculty", attr_type=AttributeTypes.str, get_generator_fun=lambda _: get_rdm_fac,
                        desc="Faculty a univ member is associated with among existing ones (not regarding uni site)")

    def get_role(given_others_attr_values):
        # the parameter should contain, for a tuple, the already generated value for matricule attribute
        matricule_value = int(given_others_attr_values["matricule"])
        is_prof = (matricule_value % 10 == 0)
        return "professor" if is_prof else "student"

    role = AttributeInfo("role", attr_type=AttributeTypes.str, get_generator_fun=lambda _: get_role, gen_order=2,
                         desc="Role of the member in the university (professor/student)")
    univ = Relation("UnivMembers", attributes=[matricule, persID, fac, role], pk=matricule)

    # --- FACULTIES
    fac_in_pk = fac.__copy__()
    fac_in_pk.desc = "An UMONS faculty"

    def get_city(_):
        return "Mons"
    city = AttributeInfo("city", attr_type=AttributeTypes.str, get_generator_fun=lambda _: get_city,
                         desc="Place where an UMONS faculty is present")

    def get_label(given_others_attr_values):
        return given_others_attr_values["city"] + '-' + given_others_attr_values["faculty"]
    label = AttributeInfo("sitelabel", attr_type='str', get_generator_fun=lambda _: get_label,
                          desc="Label used as a shortcut designing the site of a faculty")
    faculties = Relation("Faculties", attributes=[fac_in_pk, city, label], pk=[fac_in_pk, city])

    # --- USEDSITES
    shortcut = AttributeInfo("shortcut", attr_type='str', desc="Usable shortcut in a scheduling application")
    usedsites = Relation("UsedSites", attributes={"sitelabel": shortcut}, pk="sitelabel")

    # ---- FK CONSTRAINTS ----
    univ.add_fk_constraint({"faculty": faculties})
    faculties.add_fk_constraint({"sitelabel": usedsites})

    print("Relational models defined :\n", univ, faculties, usedsites, sep='\n')

    # ---- INSTANTIATION ----
    rel_inst_params = {univ: [10,
                              (1, {"matricule": 10, "persid": "remdec", "faculty": "sciences", "role": "student"}),
                              {"persid": "myprof", "faculty": "sciences", "role": "professor"}
                              ],
                       faculties: {"faculty": "sciences", "city": "Charleroi"},
                       usedsites: 0
                       }

    rel_inst_params = rel_inst_params
    db = DBInstance(rel_inst_params)
    print(db)

    degeneration_params = {univ: 5}
    db.degenerate_insts(degeneration_params)
    print(db)
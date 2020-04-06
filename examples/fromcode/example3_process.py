from src.instantiation.instparameters import GlobalParameters, TableParameters
from src.instantiation.instprocess import InstantiationProcess
from src.model.attribute import AttributeInfo as AI
from src.model.relation import Relation
from src.model.generators import get_generator_rdm_int, get_generator_increment_str
import random

if __name__ == "__main__":

    # ---- TABLE titlebasic ----
    def get_title_type(_):
        return random.choice(["movie", "short", "tvserie", "tvepisode", "video"])

    def get_title_orig(attribs):
        title = list(attribs.get("primaryTitle", "title"))
        random.shuffle(title)
        return ''.join(title)

    def get_end_year(attribs):
        if attribs["titleType"] != "tvserie":
            return "null"
        return int(attribs.get("startYear")) + random.randint(0, 20)

    def get_genre(_):
        return random.choice(['comedy', 'short', 'animation', 'documentary', 'sport', 'romance', 'drama', 'horror', 'fantasy'])

    tconst = AI("tconst", "incr_str", desc="alphanumeric unique identifier of the title")
    titleType = AI("titleType", "str", get_generator_fun=lambda _: get_title_type,
                   desc="the type/format of the title (e.g. movie, short, tvseries, tvepisode, video, etc)")
    primaryTitle = AI("primaryTitle", "word_str",
                      desc="the more popular title / the title used by the filmmakers on promotional materials at the point of release")
    originalTitle = AI("originalTitle", "word_str", get_generator_fun=lambda _: get_title_orig,
                       gen_order=2, desc="original title, in the original language")
    isAdult = AI("isAdult", "boolean", desc="0: non-adult title; 1: adult title")
    startYear = AI("startYear", "int", get_generator_fun=get_generator_rdm_int(1950, 2020),
                   desc="represents the release year of a title. In the case of TV Series, it is the series start year ")
    endYear = AI("endYear", "int", get_generator_fun=lambda _: get_end_year, gen_order=2,
                 desc="TV Series end year. ‘null’ for all other title types")
    runtimeMinutes = AI("runtimeMinutes", "int", get_generator_fun=get_generator_rdm_int(20, 360),
                        desc="primary runtime of the title, in minutes")
    genres = AI("genres", "str", get_generator_fun=lambda _: get_genre,
                desc="includes up to three genres associated with the title")

    titlebasic = Relation("titlebasic", attributes=[tconst, titleType, primaryTitle, originalTitle, isAdult, startYear,
                                                    endYear, runtimeMinutes, genres], pk=tconst)

    # ---- TABLE namebasics ----
    def get_death_year(attribs):
        deathyear = int(attribs["birthYear"]) + random.randint(10, 80)
        if deathyear < 2021:
            return deathyear
        return "null"

    def get_profession(_):
        return random.choice(['actor', 'cascador', 'matador', 'technician', 'musclor', 'princess', 'seller', 'truck'])

    nconst = AI("nconst", "incr_str",
                get_generator_fun=get_generator_increment_str(start_length=8, letters=tuple("aeiouscvbtr")),
                desc="alphanumeric unique identifier of the name/person")
    primaryName = AI("primaryName", "word_str", desc="name by which the person is most often credited")
    birthYear = AI("birthYear", "int", get_generator_fun=get_generator_rdm_int(1900, 2019),
                   desc="in YYYY format")
    deathYear = AI("deathYear", "int", get_generator_fun=get_generator_rdm_int(1900, 2019),
                   gen_order=2, desc="in YYYY format if applicable, else null")
    primaryProfession = AI("primaryProfession", "word_str", get_generator_fun=lambda _: get_profession,
                           desc="the top-3 professions of the person")
    knownForTitles = AI("knownForTitles", "word_str", desc="titles the person is known for")

    namebasics = Relation("namebasics", attributes=[nconst, primaryName, birthYear, deathYear,
                                                    primaryProfession, knownForTitles], pk=nconst)

    # ---- FK CONSTRAINTS ----
    # namebasics.add_fk_constraint({"knownForTitles": titlebasic})

    # print("Relational model :\n", titlebasic, namebasics, sep='\n')

    # A GlobalParameters allows to configure all instantiations/generations in a common way, avoiding to specify
    # a specific TableParameters for each relation. The numbers of tuples given will be equally distributed among
    # all given relation (same for part of degeneration in percentage). Many other parameters can be taken by
    # GlobalParameters and will be applied in the same way for each Relation.
    # In this case (10 tuples and 200% of degeneration), both relations will be instantiated with 5 tuples
    # and 100% of the tuples will be degenerated, ending up in tables with 5+5 tuples.
    #
    globparams = GlobalParameters(10, part_deg=200)
    instprocess = InstantiationProcess([titlebasic, namebasics], globparams)

    # This configuration with individual TableParameters for each relation will be equivalent to the
    # previous one providing only a GlobalParameters(10, part_deg=200)
    #
    # titleparams = TableParameters(10, part_deg=100)
    # nameparams = TableParameters(10, part_deg=100)
    # instprocess = InstantiationProcess([(titlebasic, titleparams), (namebasics, nameparams)])

    # This hydrid configuration is also equivalent to previous ones. For relation whose TableParameters
    # isn't given, GlobalParameters provides parameters equally distributed depending the remaining.
    # Here 10 of the 20 tuples are consumed by the specified TableParameters, and 100 of the 200 parts.
    # So for namebasics Relation, the nbr of tuples to generate is (20-10)/1 and the part to degenerate
    # is (200-100)/1 % of the 10 generated tuples.
    #
    # titleparams = TableParameters(10, part_deg=100)
    # globparams = GlobalParameters(20, part_deg=200)
    # instprocess = InstantiationProcess([(titlebasic, titleparams), namebasics], globparams)

    instprocess.instantiate_db()
    instprocess.denegerate_db()
    print(instprocess)

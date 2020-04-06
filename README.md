# ASP_DB_generator
From a given relational database schema, instantiate a fresh new ASP database, generating tuples under parametrized constraints

## What is an ASP database?

<i>Anwer Set Programming</i> if a form of declarative programming using the stable model (answer set) semantics of logic pogramming.
An ASP program can be seen as divided in 2 parts :
 * generation of possible candidates (meaning what facts are considered true)   
 * application of constraints to eliminate non matching candidates

This schema maps directly in the usage of queries on a database : the candidates are all database's tuples considered as true facts for the table they're in,
and the query is used to target some tuples on basis of query statement.

More about ASP : [wiki]("https://en.wikipedia.org/wiki/Answer_set_programming") (EN), [course](https://lucas.bourneuf.net/blog/asp-tuto.html) (FR)

We consider the usage of [clingo](https://potassco.org/) for grounding and solving ASP programs.

## Application purposes and features

This application, written in Python 3.7 (full built-in) has been released in the context of research investigations on the <i>Consistent Query Answering</i>
(see [here](https://sigmodrecord.org/publications/sigmodRecord/1909/pdfs/03_Principles_Wijsen.pdf) and [here](https://sigmodrecord.org/publications/sigmodRecord/1603/pdfs/06_Consistent_RH_Koutris.pdf))
problematic. It is used to approach the question in a practical way, as the final goal would ideally be to find solutions about querying actual inconsistent databases.

Although it exists plenty open-access databases to experiment, we don't have control on their content and inconsistency proportions.
The key idea is that, if it is desirable to experiment on actual databases to design queries that make sense, we would like
to have a full control on their content. The taken trade-off is to reuse the relational schemas of actual databases and to regenerate
tables randomly.
 
#### Control your Attributes
As in relational DB theory, we consider tables as Relations and rows as valued tuples from a set of Attributes.
From each Attribute, we are able to pull new generated values of any kind. It can be fully random but also have some sense
in continuity, like a "generator" that returns 0,1,2,3,... on consecutive calls. It allows us to define for example
attributes holding Primary Key properties. As in actual database, an Attribute
has a type associated with, indicating what is generated from. The value generation process is fully customizable,
and it includes the notion of depending on others tuple attributes values (see programmatic constraints).
 
#### Programmatic constraints
The randomness can be limited applying some programmatic constraints on generation process, saying for example
all tuples in a table that have "x_val" as value for attribute <i>x</i> will have "y_val" value for attribute <i>y</i>. This can be more advanced,
as at computing time for *y* value we dispose of *x* value ("x_val"), and so the new calculated value can be any function taking it in parameters.
For instances, Functional Dependencies in Relational DB theory can also be very easily implemented.
This feature allow us to give a meaning to data and write queries relevant to.

#### Constraints between Relations (FKs)
This implementation fully respects the Foreign Keys properties. The thing is that, when Relation *R1* has an attribute *attrFK* that
references Relation *R2* (so PK(*R2*) = *attrFK*), any tuple generated for *R1* must have an occurrence in *R2*.
Of course, only tuple's value for *attrFK* is kept, then a full tuple will be generated in *R2* (valuing others *R2* attributes).
The process is iterative, meaning that if *R2* references also another Relation, this FK constraints will be treated the same way.

#### Degeneration : generate inconsistency
Here is the crucial part for what we study : an inconsistent database has tables where 2 different tuples have the same 
values for the attribute(s) forming the PK. In other words, the PK constraint is not respected ! The process of adding inconsistencies
to a consistent database is named **degeneration**. This is done giving for each table a percentage of degeneration, related
to the number of tuples in the consistent table. This is also customizable to target specific tuples (selector function) and
randomizable. A tuple is degenerated duplicating it on basis of PK attributes, regenerating new different values for
other attributes. Once degenerated tuple is added to the table, the FKs constraints are then respected as in normal adding.

#### Application workflow
![process](process.png)

## Generate a relational database

### From scratch
It refers to the fact we define the database schema ourselves, programmaticaly or from a file written for this purpose.
Here is an example how to do it writing only Python code, from the file [example1](examples/fromcode/example1_generation.py) :
* Let's define an Attribute that will be the PK of our first Relation (the value generating function is let to default, here an
incrementer (+1) since Attribute's type is *incr_int*)
```
matricule = AttributeInfo("matricule", attr_type=AttributeTypes.incr_int,
                          desc="Registration number in university system")
```
* Here is another attribute whose generation function is given explicitly 
```
EXISTING_FACS = ["sciences", "EII", "SHS", "FPSE", "FMM"]
def get_rdm_fac(_):
    return EXISTING_FACS[randint(0, len(EXISTING_FACS)-1)]
fac = AttributeInfo("faculty", attr_type=AttributeTypes.str, get_generator_fun=lambda _: get_rdm_fac,
                    desc="Faculty a univ member is associated with among existing ones (not regarding uni site)")
```
* After defining comprising Attributes, we instantiate the Relation precising its PK
```
univ = Relation("UnivMembers", attributes=[matricule, persID, fac, role], pk=matricule)
```
* Here is an example of an attribute whose generating process depends on other attributes values (and so has a generation order > 1 that is the implicit value)
```
def get_label(given_others_attr_values):
    return given_others_attr_values["city"] + '-' + given_others_attr_values["faculty"]
label = AttributeInfo("sitelabel", attr_type='str', get_generator_fun=lambda _: get_label, gen_order=2,
                      desc="Label used as a shortcut designing the site of a faculty")
```
* A second Relation 
```
faculties = Relation("Faculties", attributes=[fac_in_pk, city, label], pk=[fac_in_pk, city])
```
* Once Relations are instantiated we can impose FKs constraints between them (here *faculty* Attribute from 
UnivMembers Relation references Faculties (one attribute in its composed PK that is *fac_in_pk*))
```
univ.add_fk_constraint({"faculty": faculties})
```
* Once all defined, we can print the relational schemas of Relations that will compose our database
```
print(univ, faculties, usedsites, sep='\n')
Relation UnivMembers| vvv PK vvv
                    | matricule : matricule [1] (INTEGER_INCR) desc : Registration number in university system
                    | vvv OTHERS vvv
                    | persid : persid [1] (STRING) desc : A personal identifier settable by the member (rdm initially)
                    | faculty : faculty [1] (STRING) desc : Faculty a univ member is associated with among existing ones (not regarding uni site) - FK for Faculties
                    | role : role [2] (STRING) desc : Role of the member in the university (professor/student)

Relation Faculties| vvv PK vvv
                  | faculty : faculty [1] (STRING) desc : An UMONS faculty
                  | city : city [1] (STRING) desc : Place where an UMONS faculty is present
                  | vvv OTHERS vvv
                  | sitelabel : sitelabel [2] (STRING) desc : Label used as a shortcut designing the site of a faculty - FK for UsedSites

Relation UsedSites| vvv PK vvv
                  | sitelabel : shortcut [1] (STRING) desc : Usable shortcut in a scheduling application
                  | vvv OTHERS vvv
```
* When we instantiate the whole database itself, we provide parameters for initial generation phase
Here it's in the simplest form, just the number of tuples to generate in. This example illustrates the iterative
process to respect FKs, as we have a chain of FKs *UnivMembers* → *Faculties* → *UsedSited*.

```
rel_inst_params = {univ: 5, faculties: 0, usedsites: 0}
db = DBInstance(rel_inst_params)
print(db)
```
```
DBInstance with 3 relation instances, generated from parameters :
>Relation UnivMembers : kept attributes=ALL | respect FK=True | params for generation=5
>Relation Faculties : kept attributes=ALL | respect FK=True | params for generation=0
>Relation UsedSites : kept attributes=ALL | respect FK=True | params for generation=0

Instance of UnivMembers, 5 tuples : 5 (regular) 0 (from constraints) 0 (degenerated)
UnivMembers | C D  [matricule] persid   <faculty> role   
            +--------------------------------------------
            |      1           JQ4SBAP4 sciences  student
            |      2           U5OUYYYX sciences  student
            |      3           8EOBMBNZ SHS       student
            |      4           W9U712J3 SHS       student
            |      5           EAV6GL2V EII       student

Instance of Faculties, 3 tuples : 0 (regular) 3 (from constraints) 0 (degenerated)
Faculties | C D  [faculty] [city] <sitelabel>  
          +------------------------------------
          | *    sciences  Mons   Mons-sciences
          | *    SHS       Mons   Mons-SHS     
          | *    EII       Mons   Mons-EII     

Instance of UsedSites, 3 tuples : 0 (regular) 3 (from constraints) 0 (degenerated)
UsedSites | C D  [sitelabel]  
          +-------------------
          | *    Mons-sciences
          | *    Mons-SHS     
          | *    Mons-EII
```

### From an existing db (MySQL, postgreSQL, ...)
This is currently not implemented, but only requires an adapted parser.
For example, treating the output of ```mysqldump --xml ...``` (see [here](https://www.eversql.com/exporting-mysql-schema-structure-to-xml-using-mysql-clients/#mysqldump)).
## Degenerate a generated database

## Write down a relational database in ASP program
Once the content of the relational database is fixed and we would like to apply ASP queries on it, 
we have to translate it in an ASP compliant format and write it in a file. Be careful that some data
will be transformed to respect ASP clingo syntax, for example constants cannot start with a capital
because it is interpreted as a variable to ground.  
This is done using 
```
write_db_inst(DBInstance(rel_big_inst_params), asp=True, printed=False, target_dir="../../outputs")
``` 
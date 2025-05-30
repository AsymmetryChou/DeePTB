# Onsite energies database, loaded from GAPW lda potentials. stored as 
# A dictionary of dictionaries. The first dictionary is the element name, and the
# second dictionary is the orbital name. The orbital name is the key, and the value is the onsite  energy.


#
# Contains the elements as follows:

#    AtomSymbol=[
#     'H',                                                                                                  'He', 
#     'Li', 'Be',                                                             'B',  'C',  'N',  'O',  'F',  'Ne', 
#     'Na', 'Mg',                                                             'Al', 'Si', 'P',  'S',  'Cl', 'Ar',
#     'K',  'Ca', 'Sc', 'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 
#     'Rb', 'Sr', 'Y',  'Zr', 'Nb', 'Mo',     , 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I',  'Xe', 
#     'Cs', 'Ba',       'Hf', 'Ta', 'W',  'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',             'Rn'
#     ]

def show_onsites(basis):
    """
    Prints the onsite energies for the given basis set
    basis = {'atom':['ns', 'np', 'nd', 'nf', 's*', 'p*', 'd*', 'f*']}
    
    Args:
        basis: The basis set to show the onsite energies for
    """
    for atom, orbs in basis.items():
        print(atom)
        for orb in onsite_energy_database[atom]:
            print(f"\t{orb}: {onsite_energy_database[atom][orb]:.4f}")

onsite_energy_database = \
{
    "H": {
        "1s": -6.353300060667574,
        "s*": 20.858024509606427,
        "p*": 0.0
    },
    "He": {
        "1s": -15.51644149646164,
        "s*": 11.69488307381236,
        "p*": 0.0
    },
    "Li": {
        "2s": -2.873787987866637,
        "2p": -1.1260046107179382,
        "s*": 24.337536582407363
    },
    "Be": {
        "2s": -5.599546370070984,
        "2p": -2.098809464105234,
        "s*": 21.61177820020302
    },
    "B": {
        "2s": -9.38300893832188,
        "2p": -3.7138015773509956,
        "s*": 17.82831563195212,
        "p*": 23.497522992923006,
        "d*": 0.0
    },
    "C": {
        "2s": -13.638587987867034,
        "2p": -5.414237249747418,
        "s*": 13.57273658240697,
        "p*": 21.797087320526582,
        "d*": 0.0
    },
    "N": {
        "2s": -18.420004132193327,
        "2p": -7.237312131368145,
        "s*": 8.791320438080675,
        "p*": 19.974012438905856,
        "d*": 0.0
    },
    "O": {
        "2s": -23.751838724881036,
        "2p": -9.195374309627717,
        "s*": 3.459485845392964,
        "p*": 18.01595026064629,
        "d*": 0.0
    },
    "F": {
        "2s": -29.646466006067826,
        "2p": -11.292971809909414,
        "s*": -2.4351414357938204,
        "p*": 15.918352760364588,
        "d*": 0.0
    },
    "Ne": {
        "2s": -36.111604610719226,
        "2p": -13.531375369060152,
        "s*": -8.90028004044522,
        "p*": 13.67994920121385,
        "d*": 0.0
    },
    "Na": {
        "3s": -2.8192864806828277,
        "3p": -0.7735868655523088,
        "s*": 24.392038089591175,
        "2p": -28.825645625250246,
        "d*": 0.0
    },
    "Mg": {
        "2s": -79.2908046599848,
        "3s": -4.7815739534885475,
        "2p": -46.72464668022558,
        "3p": -1.3736276643074314,
        "d*": 0.0,
        "s*": 22.429750616785455
    },
    "Al": {
        "3s": -7.829514418604938,
        "3p": -2.783446390293328,
        "s*": 19.38181015166906,
        "p*": 24.427878179980674,
        "d*": 0.0
    },
    "Si": {
        "3s": -10.877726996967032,
        "3p": -4.161972093023409,
        "s*": 16.333597573306967,
        "p*": 23.049352477250594,
        "d*": 0.0
    },
    "P": {
        "3s": -14.014648493428219,
        "3p": -5.596008897876849,
        "s*": 13.196676076845783,
        "p*": 21.615315672397152,
        "d*": 0.0
    },
    "S": {
        "3s": -17.278064451908673,
        "3p": -7.105937863514736,
        "s*": 9.933260118365329,
        "p*": 20.105386706759266,
        "d*": 0.0
    },
    "Cl": {
        "3s": -20.688225844287917,
        "3p": -8.70054891809941,
        "s*": 6.523098725986084,
        "p*": 18.51077565217459,
        "d*": 0.0
    },
    "Ar": {
        "3s": -24.257263174925058,
        "3p": -10.383569342770857,
        "s*": 2.954061395348946,
        "p*": 16.827755227503147,
        "d*": 0.0
    },
    "K": {
        "3s": -35.17680140559986,
        "4s": -2.427609328895759,
        "3p": -18.838516453800157,
        "p*": 8.372808116473847,
        "d*": 0.0
    },
    "Ca": {
        "3s": -46.825849452508834,
        "4s": -3.8638761110202595,
        "3p": -27.98551222657795,
        "p*": -0.7741876563039466,
        "d*": 0.0
    },
    "Sc": {
        "3s": -54.70547560176282,
        "4s": -4.292019098394871,
        "3p": -33.56786177598775,
        "4p": -1.520260945378664,
        "3d": -3.4252346625364143,
        "d*": 23.786089907737587
    },
    "Ti": {
        "3s": -62.25678948432989,
        "4s": -4.593271587462252,
        "3p": -38.7913758543998,
        "4p": -1.5355350455005619,
        "3d": -4.463201456016342,
        "d*": 22.74812311425766
    },
    "V": {
        "3s": -69.81863701805376,
        "4s": -4.845520566228692,
        "3p": -43.960799322294186,
        "4p": -1.5262831951466689,
        "3d": -5.381039433771684,
        "d*": 21.83028513650232,
        "s*": 22.365804004045312,
        "p*": 25.685041375127334
    },
    "Cr": {
        "4s": -4.190816097067899,
        "4p": -1.078929019211364,
        "3d": -3.128213872598699,
        "s*": 23.020508473206103,
        "p*": 26.13239555106264,
        "d*": 24.083110697675302
    },
    "Mn": {
        "3s": -85.3864353497258,
        "4s": -5.281718099090184,
        "3p": -54.49283076544967,
        "4p": -1.470499979777607,
        "3d": -7.008820869565475,
        "d*": 20.20250370070853,
        "s*": 21.929606471183817,
        "p*": 25.740824590496395
    },
    "Fe": {
        "4s": -5.480904994944589,
        "4p": -1.4313156723964124,
        "3d": -7.752506370071063,
        "s*": 21.73041957532941,
        "p*": 25.78000889787759,
        "d*": 19.458818200202938
    },
    "Co": {
        "4s": -5.672472719919319,
        "4p": -1.386689100101163,
        "3d": -8.461361375126701,
        "s*": 21.538851850354686,
        "p*": 25.82463547017284,
        "d*": 18.749963195147302
    },
    "Ni": {
        "4s": -5.858053953488587,
        "3p": -71.26557190406108,
        "4p": -1.3379808291203725,
        "3d": -9.140828149646442,
        "s*": 21.353270616785412,
        "d*": 18.07049642062756,
        "p*": 25.87334374115363
    },
    "Cu": {
        "4s": -4.856949322548207,
        "4p": -0.7825976946410803,
        "3d": -5.3244398786655145,
        "s*": 22.354375247725795,
        "p*": 26.428726875632922,
        "d*": 21.886884691608486
    },
    "Zn": {
        "4s": -6.2176247009809975,
        "4p": -1.2304126660884902,
        "3d": -10.425745093206796,
        "s*": 20.993699869293003,
        "p*": 25.98091190418551,
        "d*": 16.78557947706721
    },
    "Ga": {
        "4s": -9.166678907988203,
        "4p": -2.733649666329726,
        "s*": 18.0446456622858,
        "p*": 24.477674903944276,
        "d*": 0.0
    },
    "Ge": {
        "4s": -11.939784994944826,
        "4p": -4.047140303336852,
        "s*": 15.271539575329177,
        "p*": 23.16418426693715,
        "d*": 0.0
    },
    "As": {
        "4s": -14.691394135490935,
        "4p": -5.342127239636192,
        "s*": 12.519930434783069,
        "p*": 21.869197330637807,
        "d*": 0.0
    },
    "Se": {
        "4s": -17.472119393327237,
        "4p": -6.655889989889021,
        "s*": 9.739205176946768,
        "p*": 20.55543458038498,
        "d*": 0.0
    },
    "Br": {
        "4s": -20.305634620829867,
        "4p": -8.003122669363286,
        "s*": 6.905689949444136,
        "p*": 19.208201900910716,
        "d*": 0.0
    },
    "Kr": {
        "4s": -23.20581759352967,
        "4p": -9.390900222447259,
        "s*": 4.005506976744333,
        "p*": 17.82042434782674,
        "d*": 0.0
    },
    "Rb": {
        "4s": -31.955619009101273,
        "5s": -2.3624871991911887,
        "4p": -16.03481722952536,
        "p*": 11.17650734074864,
        "d*": 0.0
    },
    "Sr": {
        "4s": -40.90092478541512,
        "5s": -3.6405472266307832,
        "4p": -22.863533631002984,
        "p*": 4.347790939271018,
        "d*": 0.0
    },
    "Y": {
        "4s": -47.975538012624526,
        "5s": -4.227862369890923,
        "4p": -27.951264626996693,
        "5p": -1.496086529939509,
        "4d": -2.6447919768418857,
        "d*": 24.566532593432115
    },
    "Zr": {
        "4s": -54.49084858678083,
        "5s": -4.587283426314527,
        "4p": -32.51021664915036,
        "5p": -1.547705513870042,
        "4d": -3.7360060241765995,
        "d*": 23.475318546097405
    },
    "Nb": {
        "5s": -4.192594903405414,
        "5p": -1.2212695565193816,
        "4d": -3.2079434120433152,
        "s*": 23.018603680486184,
        "p*": 25.990080323560104,
        "d*": 24.003381158230685,
        "4s": -58.42968555745411,
        "4p": -34.61588977663103
    },
    "Mo": {
        "5s": -4.319313891757266,
        "5p": -1.1614897270570976,
        "4d": -3.933274033446238,
        "s*": 22.892071021234408,
        "p*": 26.049945237614708,
        "d*": 23.278050536827763,
        "4s": -64.38416395781437,
        "4p": -38.594991859488374
    },
    "Ru": {
        "4s": -76.3848621780856,
        "5s": -4.5072838018201855,
        "4p": -46.536018131679945,
        "5p": -1.0329418806876012,
        "4d": -5.401720040445092,
        "d*": 21.80960452982891,
        "s*": 22.704040768453815,
        "p*": 26.1783826895864
    },
    "Rh": {
        "5s": -4.581842831142737,
        "4p": -50.539960539001235,
        "5p": -0.9684510414560517,
        "4d": -6.1473103336706,
        "s*": 22.629481739131265,
        "d*": 21.064014236603402,
        "p*": 26.24287352881795
    },
    "Pd": {
        "5s": -3.6038678260870887,
        "4p": -51.370601112472926,
        "5p": -0.35619623862488664,
        "4d": -4.307552679474374,
        "s*": 23.607456744186912,
        "d*": 22.90377189079963,
        "p*": 26.855128331649112
    },
    "Ag": {
        "5s": -4.70837549039451,
        "4p": -58.67778408114238,
        "5p": -0.8438231749241968,
        "4d": -7.664069565217673,
        "s*": 22.502949079879492,
        "d*": 19.54725500505633,
        "p*": 26.367501395349805
    },
    "Cd": {
        "5s": -5.9504109556034415,
        "5p": -1.3280512245220133,
        "4d": -11.90392725985206,
        "s*": 21.26091361467056,
        "p*": 25.883273345751988,
        "d*": 15.307397310421942
    },
    "In": {
        "5s": -8.47377949572874,
        "5p": -2.6998405820777545,
        "4d": -18.72276968090763,
        "s*": 18.73754507454526,
        "p*": 24.511483988196247,
        "d*": 8.488554889366375
    },
    "Sn": {
        "5s": -10.798623186629142,
        "5p": -3.8694540308478462,
        "4d": -25.909615284125604,
        "s*": 16.412701383644862,
        "p*": 23.341870539426154,
        "d*": 1.3017092861483976
    },
    "Sb": {
        "5s": -13.069195656983348,
        "5p": -4.9944763746352,
        "4d": -33.564385140694434,
        "s*": 14.142128913290653,
        "p*": 22.2168481956388,
        "d*": -6.353060570420434
    },
    "Te": {
        "5s": -15.336819833874856,
        "5p": -6.113025666582532,
        "4d": -41.70734139535037,
        "s*": 11.874504736399146,
        "p*": 21.09829890369147,
        "d*": 0.0
    },
    "I": {
        "5s": -17.62586337714928,
        "5p": -7.240933468149912,
        "s*": 9.58546119312472,
        "p*": 19.97039110212409,
        "d*": 0.0
    },
    "Xe": {
        "5s": -19.95073141128763,
        "5p": -8.386079937909319,
        "s*": 7.26059315898637,
        "p*": 18.825244632364683,
        "d*": 0.0
    },
    "Cs": {
        "5s": -26.87145512639128,
        "6s": -2.2237094438827913,
        "5p": -13.61056032355965,
        "p*": 13.600764246714352,
        "d*": 0.0
    },
    "Ba": {
        "5s": -33.77387971688699,
        "6s": -3.3459044691608915,
        "5p": -18.81254924165893,
        "p*": 0.0,
        "d*": 0.0
    },
    "Hf": {
        "5s": -66.98743470277144,
        "6s": -5.249659727579614,
        "5p": -35.74004682580158,
        "6p": -1.4696659608979847,
        "5d": -2.8802101671589124,
        "d*": 24.331114403115087
    },
    "Ta": {
        "6s": -5.598496222613047,
        "6p": -1.4827943338554728,
        "5d": -3.7944473595612482,
        "s*": 21.61286665318583,
        "p*": 25.72857949443977,
        "d*": 23.41687721071275,
        "5s": -72.97920618769257,
        "5p": -39.58989430936922
    },
    "W": {
        "5s": -79.05242838961684,
        "6s": -5.886353731041672,
        "5p": -43.416455731302705,
        "6p": -1.4688673003033905,
        "5d": -4.693137148635158,
        "d*": 22.518187421638846,
        "s*": 21.324970839232332,
        "p*": 25.74245726997061
    },
    "Re": {
        "6s": -6.135134152179336,
        "5p": -47.24566444680034,
        "6p": -1.4394978232334221,
        "5d": -5.586495262514855,
        "s*": 21.076190418094665,
        "d*": 21.624829307759146
    },
    "Os": {
        "6s": -6.356935609371123,
        "6p": -1.400359832309069,
        "5d": -6.479991947492192,
        "s*": 20.854388960902877,
        "p*": 25.811029807887703,
        "d*": 20.73133262278181,
        "5p": -51.09231040224224
    },
    "Ir": {
        "6s": -6.559319772694065,
        "6p": -1.354691134438359,
        "5d": -7.376543812684145,
        "s*": 20.652004797579938,
        "p*": 25.85674483316576,
        "d*": 19.834780757589858,
        "5p": -54.96621211858856
    },
    "Pt": {
        "6s": -5.930201915255919,
        "6p": -0.9619949578294665,
        "5d": -6.3868557556999255,
        "s*": 21.281122655018084,
        "p*": 26.249404246714818,
        "d*": 20.82446881457408,
        "5p": -56.31832132871373
    },
    "Au": {
        "6s": -6.0479889989891,
        "6p": -0.8879055207280406,
        "5d": -7.129094924166086,
        "s*": 21.1633355712849,
        "p*": 26.323419049545958,
        "d*": 20.08222964610792
    },
    "Hg": {
        "6s": -7.093613478562374,
        "5p": -66.81677004965003,
        "6p": -1.1950254460924148,
        "5d": -10.099408659580384,
        "s*": 20.117711091711627,
        "d*": 17.111915910693618
    },
    "Tl": {
        "6s": -9.776507996112388,
        "6p": -2.584284989457381,
        "5d": -15.65424632824635,
        "s*": 17.434816574161616,
        "p*": 24.62703958081662,
        "d*": 11.557078242027652
    },
    "Pb": {
        "6s": -12.249335932518303,
        "6p": -3.7130533000464574,
        "5d": -21.326089729467377,
        "s*": 14.961988637755699,
        "p*": 23.498271270227544,
        "d*": 5.885234840806624
    },
    "Bi": {
        "6s": -14.665298733144045,
        "6p": -4.7772328380658955,
        "5d": -27.22469870814569,
        "s*": 12.546025837129957,
        "p*": 22.434091732208106,
        "d*": -0.013374137871690974
    },
    "Rn": {
        "6s": -21.998139313671206,
        "6p": -7.901548520253912,
        "s*": 5.213185256602793,
        "p*": 19.30977605002009,
        "d*": 0.0
    }
}
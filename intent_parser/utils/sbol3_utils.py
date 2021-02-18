from sbol3 import CombinatorialDerivation

def get_combinatorial_derivations(sbol_doc):
    combinatorial_derivations = []
    for sbol_obj in sbol_doc.objects:
        if type(sbol_obj) == CombinatorialDerivation:
            combinatorial_derivations.append(sbol_obj)
    return combinatorial_derivations

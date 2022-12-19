from sortedcontainers import SortedDict

def solve_coref(doc):
    solver = SortedDict()
    for chain in doc._.coref_chains.chains:
        mentions_iter = iter(chain.mentions)
        index_iter = iter(next(mentions_iter))
        base_index = next(index_iter)

        for index in index_iter:
            solver[index] = -1
        
        for mention in mentions_iter:
            index_iter = iter(mention)

            solver[next(index_iter)] = base_index
            for index in index_iter:
                solver[index] = -1

    text = []
    last_i = 0
    for solved_i, solved_code in solver.items():
        if(solved_code == -1):
            last_i = solved_i
        else:
            text.append(f"{doc[last_i:solved_i]} {doc[solved_code]}")
    return ' '.join(text)
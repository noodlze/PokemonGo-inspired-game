import json

file = open('data/pokedex.json').read()
data = json.loads(file)
new_dict = {}

# for key, val in data.items():
#     # val is a dictionary
#     info = {}
#     for k2, v2 in val.items():
#         if k2 != 'name' and k2 != 'evolve_id':
#             info[k2] = v2
#     new_dict[val['name']] = info
#     # print(val['evolve_id'])
#     # print(data[str(val['evolve_id'])])
#     info['id'] = key
#     if str(val['evolve_id']) == '0':
#         info['evolve_into'] = 'None'
#         del info['evolve_level']  # does not store the evolve_level if the pokemon doesn't evolve further
#     else:
#         info['evolve_into'] = data[str(val['evolve_id'])]['name']

with open('data/pokedex_v2.json', 'w') as f:
    f.write(json.dumps(new_dict, indent=4, sort_keys=True))

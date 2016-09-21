import json
import os

with open(os.path.join(
        os.path.dirname(__file__),
        'array_in.json'
        )) as f:
    array_in_json = f.read()
array_in_obj = json.loads(array_in_json)

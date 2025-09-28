
import json
import os

def read_json(file_path) -> dict | list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def write_json(file_path: str, data: dict | list):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



def overwrite_json(file_path : str, data : dict | list, preserve : list[str] = None):
    basedata = read_json(file_path)

    if preserve is not None:
        from zuu.u.dict_patterns import iter_nested_keys
        from zuu.std.dict import deep_set
    
        for k, v in iter_nested_keys(basedata, iter_type="both", masks=preserve):
            deep_set(data, k, v)
           

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def touch_json(file_path: str, data: dict | list):
    if not os.path.exists(file_path):
        write_json(file_path, data)

def fix_broken_json(file_path: str, data: dict | list):
    if not os.path.exists(file_path):
        write_json(file_path, data)
    else:
        try:
            read_json(file_path)
        except json.JSONDecodeError:
            write_json(file_path, data)

    
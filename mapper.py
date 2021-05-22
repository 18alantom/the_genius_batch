import abc
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import OrderedDict

CODE_DICT = {
    '1T00627': 'civil',
    '1T01417': 'mech',          # 2019
    '1T01427': 'mech',          # 2020
    '1T00727': 'comp',
    '1T00527': 'chem',
    '1T00827': 'electrical',
    '1T01227': 'it',
    '1T01027': 'extc',
    '1T01127': 'electronics',
    '3L00115': 'llb',
    '1P00137': 'bpharm',
    '2C00255': 'bcom_fm',
    '4E00143': 'bed',
    '2C00455': 'bcom_af',
    '2M00733': 'mms',
    '3A00145': 'ba',
    '2C00345': 'bcom_bi'
}

def get_csv_from_json_path(p):
    return Path(p.as_posix()[::-1].split(".", 1)[1][::-1] + ".csv")

def get_all_json(path="data"):
    return [(f, json.load(f.open())) for f in Path(path).rglob("*.json")]

def load_json(jpath):
    return (jpath, json.load(jpath.open()))

def load_all_json(root):
    return [load_json(jpath) for path in root.iterdir() for jpath in path.rglob("*.json")]

def dictify_json(json_list):
    json_dict = dict(y19={},y20={})
    for n, j in json_list:
        meta = j['meta']
        is_2020 = '2020' in meta
        is_2019 = '2019' in meta
        k = CODE_DICT[meta['code']]

        if is_2020:
            json_dict['y20'][k] = (n, j)
        elif is_2019:
            json_dict['y19'][k] = (n, j)
        else:
            raise Exception("wtf?!")
    return json_dict

class DMap(abc.ABC):
    def __init__(self, data):
        self.keys = None
        self._set_data(data)

    @abc.abstractmethod
    def _set_data(self, data):
        pass

    def __repr__(self):
        return str(self.keys)

class DCourse:
    _years = [f'20{i}'for i in range(18,22)]
    def __init__(self, stuff):
        path, data = stuff
        csv_path = get_csv_from_json_path(path)
        self.df = pd.read_csv(csv_path)
        self.meta = {}
        self._set_data(data)

    def _set_data(self, data):
        keys = []
        has_names = False
        for k in data.keys():
            if k == 'names':
                has_names = True
                continue
            setattr(self, k, data[k])
            keys.append(k)

        if has_names:
            for k in ['center', 'inst', 'dept']:
                if k in data['names']:
                    self._set_more_data(data['names'][k], k)
                    keys.append(k)
        self.keys = tuple(keys)

    def _set_more_data(self, data_dict, name):
        try:
            keys = sorted(data_dict.keys(), key=lambda x: int(x))
        except ValueError:
            keys = sorted(data_dict.keys())
        data = OrderedDict()
        for key in keys:
            try:
                data[key] = data_dict[key].split(":", 1)[1]
            except IndexError:
                data[key] = "??"
        setattr(self, name, data)

    def __repr__(self):
        s = self.meta['code']
        for y in self._years:
            if y in self.meta:
                s += f"\n{'year'.ljust(12)} : {y}"

        count = len(self.df) # stfu Pyright
        s += f"\n{'count'.ljust(12)} : {count}"

        for k,i in self.meta.items():
            if k in ['code', *self._years] or type(i) == float and np.isnan(i):
                continue
            s += f"\n{k.ljust(12)} : {i}"
        return s

class DCourses(DMap):
    def _set_data(self, data):
        self.keys = tuple(data.keys())
        for k in self.keys:
            setattr(self, k, DCourse(data[k]))

class DYear(DMap):
    def _set_data(self, data):
        self.keys = tuple(data.keys())
        for k in self.keys:
            setattr(self, k, DCourses(data[k]))

class D(DMap):
    def __init__(self, root="data"):
        root = Path(root)
        json_list = load_all_json(root)
        json_dict = dictify_json(json_list)
        self._set_data(json_dict)

    def _set_data(self, data):
        self.keys = tuple(data.keys())
        for key in self.keys:
            setattr(self, key, DCourses(data[key]))
import json
import jsonschema
import os

_schema_cache = {}


def _get_schema(name):
    if name in _schema_cache:
        return _schema_cache[name]
    path = os.path.join(os.path.dirname(__file__), name + ".json")
    with open(path, "r") as f:
        content = json.load(f)
    _schema_cache[name] = content
    return content


def validate_constraints(json_obj):
    jsonschema.validate(json_obj, _get_schema("constraints"))


def validate_core_allocations(json_obj):
    jsonschema.validate(json_obj, _get_schema("core_allocations"))


def validate_machine_graph(json_obj):
    jsonschema.validate(json_obj, _get_schema("machine_graph"))


def validate_machine(json_obj):
    jsonschema.validate(json_obj, _get_schema("machine"))


def validate_placements(json_obj):
    jsonschema.validate(json_obj, _get_schema("placements"))


def validate_routes(json_obj):
    jsonschema.validate(json_obj, _get_schema("routes"))


def validate_routing_keys(json_obj):
    jsonschema.validate(json_obj, _get_schema("routing_keys"))


def validate_routing_tables(json_obj):
    jsonschema.validate(json_obj, _get_schema("routing_tables"))


def validate_tag_allocations(json_obj):
    jsonschema.validate(json_obj, _get_schema("tag_allocations"))

class RunRequestSchema(object):

    DEFINITIONS = {
        "id": {"type": "string"},
        "comment": {"type": "string"},
        "constants": {
            "type": "object",
            "patternProperties": {
                "^[. ]*$": {"type": "string"}
            }
        },
        "clean_pipeline": {
            "type": "object",
            "properties": {
                "sessions": {"$ref": "#/definitions/clean_sessions"},
                "files": {"$ref": "#/definitions/clean_files"}
            },
            "required": ['sessions'],
            "additionalProperties": False
        },
        "raw_pipeline": {
            "type": "object",
            "properties": {
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "sessions": {"$ref": "#/definitions/raw_sessions"},
                "files": {"$ref": "#/definitions/raw_files"},
            },
            "required": ['sessions'],
            "additionalProperties": False
        },
        "clean_sessions": {
            "type": "array",
            "items": {"$ref": "#/definitions/clean_session"},
            "minItems": 1,
            "uniqueItems": True
        },
        "raw_sessions": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/raw_session"},
                    {"$ref": "#/definitions/id"}
                ]
            },
            "minItems": 1,
            "uniqueItems": True
        },
        "clean_session": {
            "type": "object",
            "properties": {
                "session_resource_set": {"$ref": "#/definitions/session_resource_set"},
                "steps": {"$ref": "#/definitions/clean_steps"}
            },
            "required": ["steps"],
            "additionalProperties": False
        },
        "raw_session": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "session_resource_set": {
                    "oneOf": [
                        {"$ref": "#/definitions/session_resource_set"},
                        {"$ref": "#/definitions/id"}
                    ]
                },
                "steps": {"$ref": "#/definitions/raw_steps"},
            },
            "required": ["steps"],
            "additionalProperties": False
        },
        "session_resource_sets": {
            "type": "array",
            "items": {"$ref": "#/definitions/session_resource_set"},
            "uniqueItems": True
        },
        "session_resource_set": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "disk_space": {"type": "string"},
                "memory": {"type": "string"},
                "cores": {"type": "integer"}
            },
            "additionalProperties": False
        },
        "step_resource_sets": {
            "type": "array",
            "items": {"$ref": "#/definitions/step_resource_set"},
            "uniqueItems": True
        },
        "step_resource_set": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "memory": {"type": "string"},
                "cores": {"type": "integer"}
            },
            "additionalProperties": False
        },
        "clean_files": {
            "type": "array",
            "items": {"$ref": "#/definitions/clean_file"},
            "minItems": 0,
            "uniqueItems": True
        },
        "raw_files": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/raw_file"},
                    {"$ref": "#/definitions/id"},
                ]
            },
            "minItems": 0,
            "uniqueItems": True
        },
        "clean_file": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "import_from": {"$ref": "#/definitions/remote_file_location"},
                "save_to": {"$ref": "#/definitions/remote_file_location"}
            },
            "required": ["path"],
            "additionalProperties": False
        },
        "raw_file": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "path": {"type": "string"},
                "import_from": {
                    "oneOf": [
                        {"$ref": "#/definitions/remote_file_location"},
                        {"$ref": "#/definitions/id"}
                    ]
                },
                "save_to": {
                    "oneOf": [
                        {"$ref": "#/definitions/remote_file_location"},
                        {"$ref": "#/definitions/id"}
                    ]
                }
            },
            "required": ["path"],
            "additionalProperties": False
        },
        "clean_steps": {
            "type": "array", 
            "items": {"$ref": "#/definitions/clean_step"},
            "minItems": 1,
            "uniqueItems": True
        },
        "raw_steps": {
            "type": "array", 
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/raw_step"},
                    {"$ref": "#/definitions/id"}
                    ]
            },
            "minItems": 1,
            "uniqueItems": True
        },
        "clean_step": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "application": {"$ref": "#/definitions/application"},
                "step_resource_set": {"$ref": "#/definitions/step_resource_set"},
                "input_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}},
                "output_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}}
            },
            "required": ["command"],
            "additionalProperties": False
        },
        "raw_step": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "command": {"type": "string"},
                "application": {
                    "oneOf": [
                        {"$ref": "#/definitions/application"},
                        {"$ref": "#/definitions/id"}
                    ]
                },
                "step_resource_set": {
                    "oneOf": [
                        {"$ref": "#/definitions/step_resource_set"},
                        {"$ref": "#/definitions/id"}
                    ]
                },
                "input_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}},
                "output_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}}
            },
            "required": ["command"],
            "additionalProperties": False
        },
        "remote_file_locations": {
            "type": "array",
            "items": {"$ref": "#/definitions/remote_file_location"}
        },
        "remote_file_location": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "path": {"type": "string"}
            },
            "required": ["path"],
            "additionalProperties": False
        },
        "applications": {
            "type": "array",
            "items": {"$ref": "#/definitions/application"}
        },
        "application": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "docker_image": {"type": "string"}
            },
            "required": ["docker_image"],
            "additionalProperties": False
        }
    }

    # No links or constants. comments and id's are removed.
    CLEAN = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "pipeline": {"$ref": "#/definitions/clean_pipeline"},
        },
        "required": ["pipeline"],
        "additionalProperties": False,
        "definitions": DEFINITIONS
    }

    # Links and constants ok. Need not be nested.
    RAW = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "comment": {"$ref": "#/definitions/comment"},
            "constants": {"$ref": "#/definitions/constants"},
            "pipeline": {"$ref": "#/definitions/raw_pipeline"},
            "applications": {"$ref": "#/definitions/applications"},
            "remote_file_locations": {"$ref": "#/definitions/remote_file_locations"},
            "files": {"$ref": "#/definitions/raw_files"},
            "session_resource_sets": {"$ref": "#/definitions/session_resource_sets"},
            "step_resource_sets": {"$ref": "#/definitions/step_resource_sets"},
            "steps": {"$ref": "#/definitions/raw_steps"},
            "sessions": {"$ref": "#/definitions/raw_sessions"},
        },
        "required": ["pipeline"],
        "additionalProperties": False,
        "definitions": DEFINITIONS
    }


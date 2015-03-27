class PipelineSchema(object):

    DEFINITIONS = {
        "id": {"type": "string"},
        "comment": {"type": "string"},
        "constants": {
            "type": "object",
            "patternProperties": {
                "^[. ]*$": {"type": "string"}
            }
        },
        "pipeline": {
            "type": "object",
            "properties": {
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "sessions": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/session"},
                    "minItems": 1,
                    "uniqueItems": True
                },
                "files": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/file"},
                    "minItems": 0,
                    "uniqueItems": True
                },
            },
            "required": ['sessions'],
            "additionalProperties": False
        },
        "pipeline_with_links": {
            "type": "object",
            "properties": {
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "sessions": {"$ref": "#/definitions/sessions_with_links"},
                "files": {"$ref": "#/definitions/files_with_links"},
            },
            "required": ['sessions'],
            "additionalProperties": False
        },
        "sessions": {
            "type": "array",
            "items": {"$ref": "#/definitions/session"},
            "minItems": 1,
            "uniqueItems": True
        },
        "sessions_with_links": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/session_with_links"},
                    {"$ref": "#/definitions/id"}
                ]
            },
            "minItems": 1,
            "uniqueItems": True
        },
        "session": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "session_resource_set": {"$ref": "#/definitions/session_resource_set"},
                "steps": {"$ref": "#/definitions/steps"}
            },
            "required": ["steps"],
            "additionalProperties": False
        },
        "session_with_links": {
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
                "steps": {"$ref": "#/definitions/steps_with_links"},
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
        "files": {
            "type": "array",
            "items": {"$ref": "#/definitions/file"},
            "minItems": 0,
            "uniqueItems": True
        },
        "files_with_links": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/file_with_links"},
                    {"$ref": "#/definitions/id"},
                ]
            },
            "minItems": 0,
            "uniqueItems": True
        },
        "file": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "path": {"type": "string"},
                "import_from": {"$ref": "#/definitions/remote_file_location"},
                "save_to": {"$ref": "#/definitions/remote_file_location"}
            },
            "required": ["path"],
            "additionalProperties": False
        },
        "file_with_links": {
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
        "steps": {
            "type": "array", 
            "items": {"$ref": "#/definitions/step"},
            "minItems": 1,
            "uniqueItems": True
        },
        "steps_with_links": {
            "type": "array", 
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/step_with_links"},
                    {"$ref": "#/definitions/id"}
                    ]
            },
            "minItems": 1,
            "uniqueItems": True
        },
        "step": {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/id"},
                "comment": {"$ref": "#/definitions/comment"},
                "constants": {"$ref": "#/definitions/constants"},
                "command": {"type": "string"},
                "application": {"$ref": "#/definitions/application"},
                "step_resource_set": {"$ref": "#/definitions/step_resource_set"},
                "input_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}},
                "output_file_ids": {"type": "array", "items": {"$ref": "#/definitions/id"}}
            },
            "required": ["command"],
            "additionalProperties": False
        },
        "step_with_links": {
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

    NO_LINKS = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "comment": {"$ref": "#/definitions/comment"},
            "constants": {"$ref": "#/definitions/constants"},
            "pipeline": {"$ref": "#/definitions/pipeline"},
        },
        "required": ["pipeline"],
        "additionalProperties": False,
        "definitions": DEFINITIONS
    }

    WITH_LINKS = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "comment": {"$ref": "#/definitions/comment"},
            "constants": {"$ref": "#/definitions/constants"},
            "pipeline": {"$ref": "#/definitions/pipeline_with_links"},
            "applications": {"$ref": "#/definitions/applications"},
            "remote_file_locations": {"$ref": "#/definitions/remote_file_locations"},
            "files": {"$ref": "#/definitions/files_with_links"},
            "session_resource_sets": {"$ref": "#/definitions/session_resource_sets"},
            "step_resource_sets": {"$ref": "#/definitions/step_resource_sets"},
            "steps": {"$ref": "#/definitions/steps_with_links"},
            "sessions": {"$ref": "#/definitions/sessions_with_links"},
        },
        "required": ["pipeline"],
        "additionalProperties": False,
        "definitions": DEFINITIONS
    }


task_run_attempt = {
    "id": "76d7a27f2d984ecbb08df87a1b3ca5b3",
    "name": "hello_step",
    "log_files": [],
    "inputs": [
        {
            "id": 1,
            "data_object": {
                "id": "4c4ed2e7b91a4cfdb7dd038f49d7117b",
                "file_content": {
                    "unnamed_file_content": {
                        "hash_value": "b1946ac92492d2347c6235b4d2611184",
                        "hash_function": "md5"
                    },
                    "filename": "hello.txt"
                },
                "file_import": {
                    "note": None,
                    "source_url": "file:///original/source//hello.txt"
                },
                "file_location": {
                    "id": "3ef8902038e043a5843529b395921df3",
                    "url": "file:///Update/this/with/actual/path",
                    "status": "complete",
                    "datetime_created": "2016-09-20T17:24:43.089754Z"
                },
                "datetime_created": "2016-09-20T17:24:43.059978Z",
                "source_type": "imported",
                "type": "file"
            },
            "type": "file",
            "channel": "hello"
        }
    ],
    "outputs": [
        {
            "id": 1,
            "data_object": None,
            "filename": "hello_cap.txt",
            "type": "file",
            "channel": "hello_cap"
        }
    ],
    "status": "not_started",
    "status_message": "Not started",
    "task_definition": {
        "inputs": [
            {
                "data_object_content": {
                    "unnamed_file_content": {
                        "hash_value": "b1946ac92492d2347c6235b4d2611184",
                        "hash_function": "md5"
                    },
                    "filename": "hello.txt"
                },
                "type": "file"
            }
        ],
        "outputs": [
            {
                "filename": "hello_cap.txt",
                "type": "file"
            }
        ],
        "environment": {
            "docker_image": "ubuntu"
        },
        "command": "cat hello.txt | tr '[a-z]' '[A-Z]' > hello_cap.txt"
    },
    "worker_process": {
        "id": "fafa5026f11a4bc2a5eebb8113dd90ba",
        "status": "not_started",
        "status_message": None,
        "container_id": None
    },
    "worker_process_monitor": {
        "id": "c3cef3526d3c4ec38840031a163112b5",
        "status": "not_started",
        "last_update": "2016-09-20T17:24:45.449099Z"
    },
    "worker_host": None
}

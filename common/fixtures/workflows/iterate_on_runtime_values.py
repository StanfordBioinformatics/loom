#!/usr/bin/env python
import uuid
import json

def _make_request():
    env = {
        'docker_image': 'ubuntu',
        }
    
    resources = {
        'memory': '1GB',
        'cores': '1',
        }
    
    split_step = {
        'name': 'split_step',
        'command': 'bamtools split -in {{ input.bam }} -tag RG; for file in *TAG_RG*.bam; do f=${file%.bam}; f=${f#*TAG_RG_}; echo $f >> {{ output_ports.chromosome_list }}; done',
        'environment': env,
        'resources': resources,
        'input_ports': [
            {
                'data_type': 'file',
                'name': 'bam',
                'file_name': 'input.bam',
                }
            ],
        'output_ports': [
            {
                'data_type': 'file_array',
                'name': 'bam_array',
                'glob': '*TAG_RG*.bam',
                },
            {
                'data_type': 'string_array',
                'name': 'chromosome_list',
                }
            ]
        }

    process_step = {
        'name': 'process_step',
        'command': 'process_chromosome {{ input_ports.bam }} > {{ output_ports.bam }}',
        'environment': env,
        'resources': resources,
        'input_ports': [
            {
                'name': 'bam',
                'type': 'file',
                'filename': '{{ input_ports.chr }}.bam',
                },
            {
                'name': 'chr',
                'type': 'string',
                }
            ],
        'output_ports': [
            {
                'name': 'bam',
                'type': 'file',
                'filename': '{{ input_ports.chr }}_out.bam',
                }
            ]
        }
    
    merge_step = {
        'name': 'merge_step',
        'command': 'samtools merge {{ output_ports.merged_bam }}{% for bam in input_ports.bam_array %} {{ bam }}{% endfor %}',
        'environment': env,
        'resources': resources,
        'input_ports': [
            {
                'name': 'bam_array',
                'data_type': 'file_array',
                'file_name': '{{ input_ports.chromosome_list[i] }}.bam',
                },
            {
                'input_ports': 'chromosome_list',
                'data_type': 'string_array'
                }
            ],
        'output_ports': [
            {
                'name': 'merged_bam',
                'file_name': 'out.bam',
                'data_type': 'file'
                }
            ]
        }
    
    split_merge_workflow = {
        'name': 'split_merge',
        'steps': [
            split_step,
            process_step,
            merge_step,
            ],
        "data_bindings": [
            {
                "destination": {
                    "step": "split_step",
                    "port": "bam"
                    }, 
                "data": {
                    "type": "file",
                    "hash_value": "???",
                    "hash_function": "md5"
                    }
                }
            ], 
        'data_pipes': [
            {
                'source': {
                    'step': 'split_step',
                    'port': 'bam_array',
                    },
                'destination': {
                    'step': 'process_step',
                    'port': 'bam',
                    }
                },
            {
                'source': {
                    'step': 'process_step',
                    'port': 'bam',
                    },
                'destination': {
                    'step': 'merge_step',
                    'port': 'bam_array',
                    }
                },
            {
                "source": {
                    "step": "split_step",
                    "port": "chromosome_list"
                    },
                "destination": {
                    "step": "process_step",
                    "port": "chr"
                    }
                },
            {
                "source": {
                    "step": "split_step",
                    "port": "chromosome_list"
                    },
                "destination": {
                    "step": "merge_step",
                    "port": "chromosome_list"
                    }
                }
            ]
        }
    
    request_run = {
        'workflows': [split_merge_workflow],
        'requester': 'someone@example.net',
        }

    return request_run

iterate_on_runtime_values = _make_request()

if __name__=='__main__':
    print json.dumps(iterate_on_runtime_values, indent=2)

from __future__ import unicode_literals

# Workflow and related objects

template_input = {
    'type': 'string',
    'channel': 'test',
    'data': {'contents': 'teststring'},
}

step_a = {
    'name': 'step_a',
    'command': 'cat {{ a1 }} {{ a2 }} > {{ b1 }}',
    'environment': {
        'docker_image': 'ubuntu'
    },
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_size': '1024' 
    },
    'inputs': [
	{
	    'channel': 'a1',
            'type': 'string',
            'hint': 'Give a file with the first integer above 0'
	},
        {
            'type': 'string',
            'data': {'contents': 'a word or two'},
            'channel': 'a2'
        }
    ],
    'outputs': [
	{
            'source': {
                'filename': 'two.txt'
            },
            'type': 'file',
	    'channel': 'b1'
	}
    ]
}


step_b = {
    'name': 'step_b',
    'command': 'cat {{ b1 }} {{ b2 }} {{ b2 }} > {{ c1 }}',
    'environment': {
        'docker_image': 'ubuntu'
    },
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_size': '1024'
    },
    'inputs': [
	{
	    'channel': 'b1',
            'type': 'file',
            'hint': 'Give a file with the first integer above 0, twice'
	},
        {
	    'channel': 'b2',
            'type': 'string',
            'hint': 'Give a file with the first integer above 0, twice'
	},
        {
            'type': 'string',
            'data': {'contents': 'more text'},
            'channel': 'b3'
        }
    ],
    'outputs': [
	{
            'source': {
                'filename': 'c1.txt'
            },
            'type': 'file',
	    'channel': 'c1'
	}
    ]
}

step_c = {
    'name': 'append_word',
    'command': 'cat {{ c1 }} > {{ result }} && echo _word >> {{ result }}',
    'environment': {
        'docker_image': 'ubuntu'
    },
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_size': '1024'
    },
    'inputs': [
	{
	    'channel': 'c1',
            'type': 'file',
            'hint': 'here is what you should enter'
	}
    ],
    'outputs': [
	{
            'source': {
                'filename': 'result.txt'
            },
	    'channel': 'result',
            'type': 'file'
	}
    ]
}


flat_workflow = {
    'name': 'flat',
    'inputs': [
        {
            'hint': 'Any text',
            'type': 'string',
            'channel': 'a1'
        },
	{
            'type': 'string',
	    'data': {'contents': 'two'},
	    'channel': 'b2'
	}
    ],
    'outputs': [
	{
	    'channel': 'c1',
            'type': 'file'
	}
    ],
    'steps': [
        step_a,
        step_b
    ]
}

nested_workflow = {
    'name': 'nested',
    'inputs': [
        {
            'type': 'string',
            'channel': 'a1',
            'data': {'contents': 'a1 text'}
        }
    ],
    'outputs': [
        {
            'channel': 'result',
            'type': 'file'
        }
    ],
    'steps': [
        flat_workflow,
        step_c
    ]
}

big_workflow_steps = []
for i in range(50):
    big_workflow_steps.append(
        {
            'name': 'step_%s' % i,
            'command': 'cat {{ a }} > {{ b%s }}' % i,
            'environment': {
                'docker_image': 'ubuntu'
            },
            'resources': {
                'cores': '1',
                'memory': '1',
                'disk_size': '1024' 
            },
            'inputs': [
                {
                    'type': 'string',
                    'data': {'contents': 'a word or two'},
                    'channel': 'a'
                }
            ],
            'outputs': [
                {
                    'source': {
                        'filename': 'two.txt'
                    },
                    'type': 'file',
                    'channel': 'b%s' %i
                }
            ]
        }
    )

big_workflow = {
    'name': 'big',
    'outputs': [
        {
            'channel': 'b0',
            'type': 'file'
        }
    ],
    'steps': big_workflow_steps
}

duplicate_channels = {
    'name': 'duplicate_channels',
    'command': 'echo',
    'environment': {
        'docker_image': 'ubuntu'
    },
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_size': '1024' 
    },
    'inputs': [
	{
	    'channel': 'dup',
            'type': 'string',
            'hint': 'Give a file with the first integer above 0'
	}
    ],
    'outputs': [
	{
            'source': {
                'filename': 'out.txt'
            },
            'type': 'string',
	    'channel': 'dup'
	}
    ]
}

duplicate_sources = {
    'name': 'duplicate_sources',
    'command': 'echo',
    'environment': {'docker_image': 'ubuntu'},
    'inputs': [{'channel': 'dup', 'type': 'string'},
               {'channel': 'one', 'type': 'string'},],
    'steps': [
        {
            'name': 'child1',
            'command': 'echo',
            'environment': {'docker_image': 'ubuntu'},
            'inputs': [{'channel': 'one', 'type': 'string'},],
            'outputs': [{'channel': 'dup', 'type': 'string'},],
        }
    ],
}

no_source = {
    'name': 'no_source',
    'command': 'echo',
    'environment': {'docker_image': 'ubuntu'},
    'inputs': [{'channel': 'one', 'type': 'string'},],
    'steps': [
        {
            'name': 'child1',
            'command': 'echo',
            'environment': {'docker_image': 'ubuntu'},
            'inputs': [{'channel': 'two', 'type': 'string'},],
            'outputs': [{'channel': 'three', 'type': 'string'},],
        }
    ],
}

source_type_mismatch = {
    'name': 'source_type_mismatch',
    'inputs': [{'channel': 'one', 'type': 'boolean'},],
    'steps': [
        {
            'name': 'child1',
            'command': 'echo',
            'environment': {'docker_image': 'ubuntu'},
            'inputs': [{'channel': 'one', 'type': 'string'},],
            'outputs': [{'channel': 'three', 'type': 'string'},],
        }
    ],
}

missing_file_reference = {
    'name': 'missing_file_reference',
    'command': 'echo',
    'environment': {'docker_image': 'ubuntu'},
    'inputs': [{'channel': 'one', 'type': 'file', 'data': {'contents': 'missingfile.txt'}},],
}

missing_template_reference = {
    'name': 'no_source',
    'inputs': [{'channel': 'one', 'type': 'string'},],
    'steps': ['stepone',],
}

input_dimension_mismatch = {
    'name': 'input_dimension_mismatch',
    'command': 'echo',
    'environment': {'docker_image': 'ubuntu'},
    'inputs': [
        {'channel': 'one', 'type': 'integer', 'group': 0, 'data': {'contents': [[1,2,3],[4,5]]}},
        {'channel': 'two', 'type': 'integer', 'group': 0, 'data': {'contents': [[1,2],[3,4]]}},
    ],
}

has_cycle = {
    'name': 'has_cycle',
    'steps': [
        {
            'name': 'child1',
            'command': 'echo',
            'environment': {'docker_image': 'ubuntu'},
            'inputs': [{'channel': 'one', 'type': 'string'},],
            'outputs': [{'channel': 'two', 'type': 'string'},],
        },
        {
            'name': 'child2',
            'command': 'echo',
            'environment': {'docker_image': 'ubuntu'},
            'inputs': [{'channel': 'two', 'type': 'string'},],
            'outputs': [{'channel': 'one', 'type': 'string'},],
        }
    ],
}

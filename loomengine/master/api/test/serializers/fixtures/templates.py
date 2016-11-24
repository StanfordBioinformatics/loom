from __future__ import unicode_literals

# Workflow and related objects

fixed_step_input = {
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
	}
    ],
    'fixed_inputs': [
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
	}
    ],
    'fixed_inputs': [{
        'type': 'string',
        'data': {'contents': 'more text'},
        'channel': 'b3'
    }],
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
        }
    ],
    'fixed_inputs': [
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
    'fixed_inputs': [
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

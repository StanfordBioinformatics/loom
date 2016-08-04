# Workflow and related objects

fixed_step_input = {
    'type': 'string',
    'channel': 'test',
    'value': 'teststring',
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
        'disk_space': '1024' 
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
            'value': 'a word or two',
            'channel': 'a2'
        }
    ],
    'outputs': [
	{
            'filename': 'two.txt',
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
        'disk_space': '1024'
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
        'value': 'more text',
        'channel': 'b3'
    }],
    'outputs': [
	{
            'filename': 'c1.txt',
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
        'disk_space': '1024'
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
            'filename': 'result.txt',
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
	    'value': 'two',
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
            'value': 'a1 text'
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

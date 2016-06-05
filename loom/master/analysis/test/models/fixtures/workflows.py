from .data_objects import file

# Workflow and related objects

step_a = {
    'name': 'step_a',
    'command': 'cat {{ a1 }} {{ a2 }} > {{ a3 }}',
    'environment': {
        'docker_image': 'ubuntu'
    },
    'resources': {
        'cores': 1,
        'memory': '1',
        'disk_space': '1024' 
    },
    'inputs': [
	{
	    'channel': 'a1',
            'type': 'file',
            'hint': 'Give a file with the first integer above 0'
	}
    ],
    'fixed_inputs': [{
        'type': 'file',
        'id': 'myfile.txt@12345',
        'channel': 'a2'
    }],
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
        'cores': 1,
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
            'type': 'file',
            'hint': 'Give a file with the first integer above 0, twice'
	}

    ],
    'fixed_inputs': [{
        'type': 'file',
        'id': 'myfile.txt@12345',
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
        'cores': 1,
        'memory': '1',
        'disk_space': '1024'
    },
    'inputs': [
	{
	    'channel': 'c1',
            'type': 'file'
	}
    ],
    'outputs': [
	{
            'filename': 'result.txt',
	    'channel': 'result'
	}
    ]
}


flat_workflow = {
    'name': 'flat',
    'inputs': [
        {
            'hint': 'Any file',
            'type': 'file',
            'channel': 'a1'
        }
    ],
    'fixed_inputs': [
	{
            'type': 'file',
	    'id': 'one.txt@c4f3f632b7b503149f88d9de9f9bd0927a066ee935fdc011a75ff4a216d6e061',
	    'channel': 'b2'
	}
    ],
    'outputs': [
	{
	    'channel': 'c1'
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
            'type': 'file',
            'channel': 'a1',
            'id': 'input.txt@123'
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

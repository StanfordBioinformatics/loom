#!/usr/bin/env python

workflow_run_struct = {
    'workflow_run_inputs': [
	{
	    'workflow_input': {
		u'type': u'file',
		u'prompt': u"Enter the 'hello' file",
		u'to_channel': u'hello'
	    },
	    'data_object': {
		u'filename': u'hello.txt',
		u'file_contents': {
		    u'hash_value': u'b1946ac92492d2347c6235b4d2611184',
		    u'hash_function': u'md5'},
	    }
	}
    ],
    'workflow': {
	u'steps': [
	    {
		u'environment': {
		    u'docker_image': u'ubuntu'
		},
		u'command': u'echo world > {{ world }}',
		u'step_name': u'world_step',
		u'resources': {
		    u'cores': 1,
		    u'memory': u'1GB'
		},
		u'step_outputs': [
		    {
			u'from_path': u'world.txt',
			u'to_channel': u'world',
		    }
		]
	    },
	    {
		u'step_inputs': [
		    {
			u'from_channel': u'hello',
		    },
		    {
			u'from_channel': u'world',
		    }
		],
		u'environment': {
		    u'docker_image': u'ubuntu'
		}, u'command': u'cat {{ hello }} {{ world }} > {{ hello_world }}',
		u'step_name': u'hello_world_step',
		u'resources': {
		    u'cores': 1,
		    u'memory': u'1GB'
		},
		u'step_outputs': [
		    {
			u'from_path': u'hello_world.txt',
			u'to_channel': u'hello_world_out',
		    }
		]
	    }
	],
	u'workflow_name': u'hello_world',
	u'workflow_outputs': [
	    {
		u'from_channel': u'hello_world_out',
		u'output_name': u'hello_world'
	    }
	],
	u'workflow_inputs': [
	    {
		u'type': u'file',
		u'prompt': u"Enter the 'hello' file",
		u'to_channel': u'hello'
	    }
	]
    }
}

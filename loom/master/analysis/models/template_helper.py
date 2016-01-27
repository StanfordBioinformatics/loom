from jinja2 import DictLoader, Environment

class StepTemplateContext:
    """Utilities to perform substitutions on user-provided
    text in the Step.
    """

    def __init__(self, step, input_set):
        self.step = step
        self.input_set = input_set

    def get_context(self):
        return {
            'input_ports': self._get_input_ports_context(),
            'output_ports': self._get_output_ports_context(),
            'constants': self._get_constants_context(),
            }

    def _get_input_ports_context(self):
        input_ports_context = {}
        for port in self.step.input_ports.all():
            input_ports_context[port.name] = self._get_input_port_context(port)
        return input_ports_context

    def _get_input_port_context(self, port):
        if port.is_array:
            return self._get_array_input_port_context(port)
        else:
            return self._get_scalar_input_port_context(port)

    def _get_scalar_input_port_context(self, port):
        return {
            'file_name': port.file_name
            }

    def _get_array_input_port_context(self, port):
        data_object = self.input_set.get_data_object(port.name)
        if data_object.is_array():
            return [{'file_name': name}
                    for name in self.get_file_name_list(data_object, port.file_name)]
        else:
            return {'file_name': port.file_name}

    @classmethod
    def get_file_name_list(cls, data_object, file_name_prefix):
        if data_object.is_array():
            return [
                "%s_%s" % (i+1, file_name_prefix)
                for i in range(data_object.files.count())
                ]
        else:
            return [file_name_prefix]

    def _get_output_ports_context(self):
        output_ports_context = {}
        for port in self.step.output_ports.all():
            output_ports_context[port.name] = self._get_output_port_context(port)
        return output_ports_context

    def _get_output_port_context(self, port):
        return {
            'file_name': port.file_name
            }

    def _get_constants_context(self):
        constants = self._get_workflow_constants()
        constants.update(self._get_step_constants())
        return constants

    def _get_step_constants(self):
        if self.step.constants is not None:
            return self.step.constants
        return {}

    def _get_workflow_constants(self):
        if self.step.workflow is not None:
            if self.step.workflow.constants is not None:
                return self.step.workflow.constants
        return {}


class StepTemplateHelper:

    def __init__(self, step, input_set):
        self.step = step
        self.context = StepTemplateContext(self.step, input_set).get_context()

    def render(self, template_string):
        if template_string == None:
            return None
        max_iter = 1000
        counter = 0
        while True:
            counter += counter
            updated_template_string = self._render_once(template_string)
            if updated_template_string == template_string:
                return template_string
            if counter > max_iter:
                raise Exception("There appears to be a cyclical reference in your {{ templates }}. "
                                "Maximum iterations exceeded in rendering a template string for this step: %s" % step.to_struct())
            template_string = updated_template_string

    def _render_once(self, template_string):
        loader = DictLoader({'template': template_string})
        env = Environment(loader=loader)
        template = env.get_template('template')
        return template.render(**self.context)

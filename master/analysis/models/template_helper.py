from jinja2 import DictLoader, Environment

class StepTemplateContext:

    def __init__(self, step):
        self.step = step

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
        # if 1 to 1, get_scalar
        # if 1 to many, get scalar
        # if array to 1, get array
        # if array to array, get scalar
#        if port.is_from_scalar():
#            return self._get_scalar_input_port_context(port)
#        else:
#            return self._get_array_input_port_context(port)
        return self._get_scalar_input_port_context(port)

    def _get_scalar_input_port_context(self, port):
        return {
            'file_path': port.file_path
            }

#    def _get_array_input_port_context(self, port):
#        return {
#            'file_path': []
#            }

    def _get_output_ports_context(self):
        output_ports_context = {}
        for port in self.step.output_ports.all():
            output_ports_context[port.name] = self._get_output_port_context(port)
        return output_ports_context

    def _get_output_port_context(self, port):
        return {
            'file_path': port.file_path
            }

    def _get_constants_context(self):
        constants = self._get_request_submission_constants()
        constants.update(self._get_workflow_constants())
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

    def _get_request_submission_constants(self):
        if self.step.workflow is not None:
            if self.step.workflow.request_submission is not None:
                if self.step.workflow.request_submission.constants is not None:
                    return self.step.workflow.request_submission.constants
        return {}

class StepTemplateHelper:

    def __init__(self, step):
        self.step = step
        self.context = StepTemplateContext(self.step).get_context()

    def render(self, template_string):
        max_iter = 1000
        counter = 0
        while True:
            counter += counter
            updated_template_string = self._render_once(template_string)
            if updated_template_string == template_string:
                return template_string
            if counter > max_iter:
                raise Exception("There appears to be a cyclical reference in your {{ templates }}. "
                                "Maximum iterations exceeded in rendering a template string for this step: %s" % step.to_obj())
            template_string = updated_template_string

    def _render_once(self, template_string):
        loader = DictLoader({'template': template_string})
        env = Environment(loader=loader)
        template = env.get_template('template')
        return template.render(**self.context)

class DelimitedParser(object):

    def __init__(self, options, text):
        self.options = options
        self.text = text

    def parse(self):
	delimiter = self.options.get('delimiter')
        if delimiter is None:
            raise Exception('"delimiter" is a required option for a parser of '\
                            'type "delimited"')
	trim = self.options.get('trim')

        text_array = self.text.split(delimiter)
        if trim:
            text_array = [item.strip() for item in text_array]
        return text_array

parser_classes = {
    'delimited': DelimitedParser
}

def _get_parser_class(parser_type):
    if not parser_type in parser_classes.keys():
        raise Exception('Unknown parser type "%s"' % parser_type)
    return parser_classes[parser_type]

def parse_output(parser_obj, text):
    Parser = _get_parser_class(parser_obj.get('type'))
    return Parser(parser_obj.get('options'), text).parse()

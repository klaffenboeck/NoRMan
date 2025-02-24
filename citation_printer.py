import json
import re
#import bibtexparser
#from authors import Author, AuthorList
from config_handler import ConfigHandler
#from bibtex_formatter import *
from output_formatter import OutputFormatterFactory, PlainFormatter
#from collections import Counter
#from nltk.corpus import stopwords
#from nltk.tokenize import word_tokenize

__all__ = ["CitationPrinter"]

class CitationPrinter:
    def __init__(self, reference, config_path: str = "configs/config.json", style_config: str = "formatting_styles.json"):
        self.reference = reference
        self.config_path = config_path
        self.style_config_path = style_config
        self.style_config_data = ConfigHandler.load_config(self.style_config_path)

        #self.bibtex_formatter = None
        self.output_formatter = PlainFormatter()



    #key = property(lambda self: self.citation_key)
    #cite_count = property(lambda self: self.count)


    def reload_config(self):
        """Reloads the style configuration from the JSON file."""
        ConfigHandler.reload_config()
        self.style_config_data = ConfigHandler.load_config(self.style_config_path)


    def get(self, key, *args, **kwargs):
        print(f"Resolving {key} with args={args} and kwargs={kwargs}")
        if '.' in key:
            obj, method = key.split('.', 1)
            print(f"Object: {obj}, Method: {method}")

            obj_ref = getattr(self.reference, obj, None)
            if obj_ref:
                print(f"Found object: {obj_ref}")
                if hasattr(obj_ref, method):
                    print(f"Calling method: {method} on {obj}")
                    return getattr(obj_ref, method)(*args, **kwargs)
                else:
                    print(f"Method {method} not found on {obj}")
            else:
                print(f"Object {obj} not found in CitationManager")

        formatter = kwargs.get("formatter", None)
        if formatter:
            value = getattr(self.reference, key, '')
            # HACK: should actually take the object
            value = formatter.format_key(key, value)
            return value
        else:
            value = getattr(self.reference, key, '')
            print(f"Returning direct attribute: {value}")
            return value

    def select_style_template(self, **kwargs) -> str:
        style = kwargs.get("style", "APA")
        type = kwargs.get("type", "reference")
        encoding = kwargs.get("encoding", "default")  # Reserved for future use
        bib_type = kwargs.get("bib_type", "default")  # E.g., article, book, inproceedings

        style_data = self.style_config_data.get("journal_formatting_styles", {}).get(style, {})
        type_data = style_data.get(bib_type, style_data.get("default", {}))

        template = type_data.get(type, "")
        #breakpoint()
        return template

    def process_citation(self, **kwargs):
        print("CALLED PROCESS_CITATION")
        template_str = self.select_style_template(**kwargs)
        formatter = kwargs.get("formatter", "plain")
        self.output_formatter = OutputFormatterFactory.get_formatter(formatter)

        def replace_conditionals(text):
            pattern = re.compile(r'\{\{(.*?)((?:##.*?##|\{\{.*?\}\})+)(.*?)\}\}', re.DOTALL)

            def conditional_replacer(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)

                markers = re.findall(r'##(.*?)##', content)

                if all(self.get(marker.strip(), formatter=self.output_formatter) for marker in markers):
                    content = replace_conditionals(content)
                    for marker in markers:
                        content = content.replace(f'##{marker}##', self.get(marker.strip(), formatter=self.output_formatter))
                    return f"{prefix}{content}{suffix}"
                return ''

            return pattern.sub(conditional_replacer, text)

        def replace_variables(text):
            pattern = re.compile(r'##(.*?)##')

            def variable_replacer(match):
                key = match.group(1).strip()
                #breakpoint()
                return self.get(key, formatter=self.output_formatter)

            return pattern.sub(variable_replacer, text)

        def postprocess(text):
            # Check for final marker {{{.}}} and extract the desired final symbol
            final_marker_match = re.search(r'\{\{\{(.*?)\}\}\}$', text)
            final_symbol = final_marker_match.group(1) if final_marker_match else ''

            # Remove final marker from the text
            text = re.sub(r'\{\{\{.*?\}\}\}$', '', text)

            # Replace trailing non-alphanumeric characters, preserving ), ], >
            text = re.sub(r'([^\w\)\]\>]+)$', '', text)

            # Append the final symbol if it exists
            if final_symbol:
                # if text.endswith((')', ']', '>')):
                #     text = text[:-1] + final_symbol + text[-1]
                # else:
                text += final_symbol

            if self.output_formatter:
                return self.output_formatter.format_final_entry(text, id=self.reference.key)
            else:
                return text

        processed = replace_conditionals(template_str)
        processed = replace_variables(processed)
        processed = postprocess(processed)
        return processed

    cite = process_citation

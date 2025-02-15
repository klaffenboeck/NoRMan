class FormattedTextPart:
    def __init__(self, content, format_type, encoded_content):
        self.content = content
        self.format_type = format_type  # e.g., 'italic', 'bold', 'underscore', 'typed'
        self.encoded_content = encoded_content  # The original encoded content (e.g., <i>italic</i>, \textit{italic}, *italic*)

    def __str__(self):
        return self.content

    def __repr__(self):
            return f"FormattedTextPart(content='{self.content}', format_type='{self.format_type}'), encoded_content='{self.encoded_content}'"

class MarkupText:
    def __init__(self, text):
        self.original_text = text
        self.italic_parts = []
        self.bold_parts = []
        self.underscored_parts = []
        self.typed_parts = []
        self.strikethrough_parts = []
        self.plain_text = text

        # Start parsing
        self.parse()

    def parse(self):
        self._parse_html()
        self._parse_latex()
        self._parse_markdown()

    def to_preformatted_html(self):
        return self._format_output('<i>{}</i>', '<b>{}</b>', '<u>{}</u>', '<code>{}</code>', '<s>{}</s>')


    def to_preformatted_latex(self):
        return self._format_output('\\textit{{{}}}', '\\textbf{{{}}}', '\\underline{{{}}}', '\\texttt{{{}}}', '\\st{{{}}}')

    # FIXME: to_formatted_markdown is still buggy
    def to_preformatted_markdown(self):
        return self._format_output('*{}*', '**{}**', '_{}_', '`{}`', '~~{}~~')

    def to_plain_html(self):
        return self._simple_format_output('<i>{}</i>', '<b>{}</b>', '<u>{}</u>', '<code>{}</code>', '<s>{}</s>')

    def to_plain_latex(self):
        return self._simple_format_output('\\textit{{{}}}', '\\textbf{{{}}}', '\\underline{{{}}}', '\\texttt{{{}}}', '\\st{{{}}}')

    def to_plain_markdown(self):
        return self._simple_format_output('*{}*', '**{}**', '_{}_', '`{}`', '~~{}~~')

    def _simple_format_output(self, italic_format, bold_format, underscore_format, typed_format, strikethrough_format):
        formatted_text = self.plain_text
        for part in self.italic_parts:
            formatted_text = formatted_text.replace(part.content, italic_format.format(part.content))
        for part in self.bold_parts:
            formatted_text = formatted_text.replace(part.content, bold_format.format(part.content))
        for part in self.underscored_parts:
            formatted_text = formatted_text.replace(part.content, underscore_format.format(part.content))
        for part in self.typed_parts:
            formatted_text = formatted_text.replace(part.content, typed_format.format(part.content))
        for part in self.strikethrough_parts:
            formatted_text = formatted_text.replace(part.content, strikethrough_format.format(part.content))
        return formatted_text

    def _format_output(self, italic_format, bold_format, underscore_format, typed_format, strikethrough_format):
        formatted_text = self.original_text
        for part in self.italic_parts:
            formatted_text = formatted_text.replace(part.encoded_content, italic_format.format(part.content))
        for part in self.bold_parts:
            formatted_text = formatted_text.replace(part.encoded_content, bold_format.format(part.content))
        for part in self.underscored_parts:
            formatted_text = formatted_text.replace(part.encoded_content, underscore_format.format(part.content))
        for part in self.typed_parts:
            formatted_text = formatted_text.replace(part.encoded_content, typed_format.format(part.content))
        for part in self.strikethrough_parts:
            formatted_text = formatted_text.replace(part.encoded_content, strikethrough_format.format(part.content))
        return formatted_text

    def _parse_html(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(self.plain_text, 'html.parser')

        # Extract parts
        for tag in soup.find_all(['i', 'b']):
            part = FormattedTextPart(tag.get_text(), tag.name, str(tag))
            if tag.name == 'i':
                self.italic_parts.append(part)
            if tag.name == 'b':
                self.bold_parts.append(part)
            if tag.name == 'i' and tag.find('b') or tag.name == 'b' and tag.find('i'):
                self.italic_parts.append(part)
                self.bold_parts.append(part)

        self.underscored_parts += [FormattedTextPart(tag.get_text(), 'underscore', str(tag)) for tag in soup.find_all('u')]
        self.typed_parts += [FormattedTextPart(tag.get_text(), 'typed', str(tag)) for tag in soup.find_all('code')]
        self.strikethrough_parts += [FormattedTextPart(tag.get_text(), 'strikethrough', str(tag)) for tag in soup.find_all('s')]

        # Strip HTML tags
        self.plain_text = soup.get_text().strip()

    def _parse_latex(self):
        from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexCharsNode

        walker = LatexWalker(self.plain_text)
        nodes, _, _ = walker.get_latex_nodes()

        plain_text_parts = []

        for node in nodes:
            if isinstance(node, LatexMacroNode):
                content = ''.join(child.chars for child in node.nodeargd.argnlist[0].nodelist)

                if node.macroname == 'textit':
                    part = FormattedTextPart(content, 'italic', f"\\textit{{{content}}}")
                    self.italic_parts.append(part)
                elif node.macroname == 'textbf':
                    part = FormattedTextPart(content, 'bold', f"\\textbf{{{content}}}")
                    self.bold_parts.append(part)
                elif node.macroname == 'underline':
                    part = FormattedTextPart(content, 'underscore', f"\\underline{{{content}}}")
                    self.underscored_parts.append(part)
                elif node.macroname == 'texttt':
                    part = FormattedTextPart(content, 'typed', f"\\texttt{{{content}}}")
                    self.typed_parts.append(part)
                elif node.macroname in ['st', 'sout']:
                    part = FormattedTextPart(content, 'strikethrough', f"\\{node.macroname}{{{content}}}")
                    self.strikethrough_parts.append(part)

                # Add formatted content to plain text
                plain_text_parts.append(content)

            elif isinstance(node, LatexCharsNode):
                # Add unformatted text
                plain_text_parts.append(node.chars)

        # Combine all text parts (formatted and unformatted)
        self.plain_text = ''.join(plain_text_parts).strip()


    # TODO: check that _parse_markdown is actually working properly
    def _parse_markdown(self):
        import mistune

        # Create the Markdown parser with AST renderer
        markdown_parser = mistune.create_markdown(renderer='ast')
        parsed = markdown_parser(self.plain_text)

        # Initialize raw text as an empty string
        raw_text = ""

        # Recursive function to process text while maintaining order
        def extract_text(node):
            nonlocal raw_text  # Use the raw_text variable across recursive calls

            if isinstance(node, list):  # If it's a list of nodes, iterate over them
                for child in node:
                    extract_text(child)
            elif isinstance(node, dict):  # If it's a single node
                if node.get('type') == 'text':  # Plain text
                    raw_text += node['raw']
                elif node.get('type') == 'codespan':  # Inline code
                    content = node['raw']
                    part = FormattedTextPart(content, 'typed', f"`{content}`")
                    self.typed_parts.append(part)
                    raw_text += content
                elif node.get('type') == 'emphasis' and 'children' in node:
                    content = node['children'][0]['raw']
                    part = FormattedTextPart(content, 'italic', f"*{content}*")
                    self.italic_parts.append(part)
                    raw_text += content  # Append in order
                elif node.get('type') == 'strong' and 'children' in node:
                    content = node['children'][0]['raw']
                    part = FormattedTextPart(content, 'bold', f"**{content}**")
                    self.bold_parts.append(part)
                    raw_text += content  # Append in order
                elif node.get('type') == 'delete' and 'children' in node:
                    content = node['children'][0]['raw']
                    part = FormattedTextPart(content, 'strikethrough', f"~~{content}~~")
                    self.strikethrough_parts.append(part)
                    raw_text += content  # Append in order
                elif 'children' in node and isinstance(node['children'], list):
                    extract_text(node['children'])  # Recursively process children

        # Extract text from AST
        extract_text(parsed)

        # Set the dynamically built plain text
        self.plain_text = raw_text.strip()

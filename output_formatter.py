from abc import ABC, abstractmethod
import re
import sys

__all__ = [
    "OutputFormatter",
    "PlainFormatter",
    "HtmlFormatter",
    "HtmlCssFormatter",
    "LatexFormatter",
    "MarkdownFormatter",
    "OutputFormatterFactory"
]


class OutputFormatter(ABC):
    @classmethod
    def get_formatter(cls, key):
        """Retrieves the appropriate formatter from the factory."""
        return OutputFormatterFactory.get_formatter(key)

    def format_author(self, author, *args, **kwargs):
        return author._format(*args, **kwargs)

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)

    def format_key(self, key, value):
        print(f"called formatter with {key} and {value}")
        return str(value)

    def format_final_entry(self, entry, reference, *args, **kwargs):
        return entry

    def append_link(self, entry, reference, *args):
        if "reference" in args and reference.link_doi:
            return f"{entry} <<{reference.link_doi}>>"
        return entry


class PlainFormatter(OutputFormatter):
    pass


class HtmlFormatter(OutputFormatter):

    def append_link(self, entry, reference, *args):
        if not reference.link_doi:
            return entry
        html_link = '<a href="{0}">{0}</a>'
        if "reference" in args:
            html_link = html_link.format(reference.link_doi)
        else:
            html_link = f'[<a href="{reference.link_doi}">&gt;</a>]'
        return f"{entry} {html_link}"




class HtmlCssFormatter(HtmlFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        css_class = author.css_class()
        return f"<span class='author {css_class}'>{formatted_author}</span>"

    def format_authors(self, author_list, *args, **kwargs):
        formatted_authors = author_list._format(*args, **kwargs)
        return f"<span class='authors'>{formatted_authors}</span>"

    # HACK: should actually take the entire object and process it properly
    def format_key(self, key, value):
        return f"<span class='{key}'>{value}</span>"

    def format_final_entry(self, entry, reference, *args, **kwargs):
        id = reference.key
        if "Link" in args:
            return f"<div id='{id}>{entry}"
        else:
            return f"<div id='{id}>{entry}</div>"

    def append_link(self, entry, reference, *args):
        if not reference.link_doi:
            return entry
        html_link = '<span class="{0}><a href="{1}">{1}</a></span></div>'
        if "reference" in args:
            html_link = html_link.format("link doi", reference.link_doi)
        else:
            html_link = f'<span class="link>[<a href="{reference.link_doi}">&gt;</a>]</span></div>'
        return f"{entry} {html_link}"


# class LatexFormatter(OutputFormatter):
#     def format_author(self, author, *args, **kwargs):
#         formatted_author = author._format(*args, **kwargs)
#         return f"{formatted_author}"

#     def format_authors(self, author_list, *args, **kwargs):
#         return author_list._format(*args, **kwargs)

#     def format_final_entry(self, text, *args, **kwargs):
#         """
#         Replaces specific HTML-style formatting tags with LaTeX equivalents.
#         Fixes escaping issues by properly handling replacement values.
#         """
#         replacements = {
#             r"<i>": r"\\textit{",    # Double escaping ensures LaTeX compatibility
#             r"</i>": r"}",
#             r"<b>": r"\\textbf{",
#             r"</b>": r"}",
#             r"<u>": r"\\underline{",
#             r"</u>": r"}"
#         }

#         # Apply replacements with correct escaping
#         for html_tag, latex_equiv in replacements.items():
#             text = re.sub(re.escape(html_tag), latex_equiv, text)  # Escape search patterns, not replacement values

#         return text

#     def append_link


class LatexFormatter(OutputFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        return f"{formatted_author}"

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)

    def format_final_entry(self, text, reference, *args, **kwargs):
        """
        Replaces HTML-style formatting tags with LaTeX equivalents
        and escapes a basic set of special LaTeX characters.
        """
        # HTML to LaTeX replacements
        replacements = {
            r"<i>": r"\\textit{",    # Double escaping ensures LaTeX compatibility
            r"</i>": r"}",
            r"<b>": r"\\textbf{",
            r"</b>": r"}",
            r"<u>": r"\\underline{",
            r"</u>": r"}"
        }

        # Apply replacements for HTML tags first
        for special_tag, latex_equiv in replacements.items():
            text = re.sub(re.escape(special_tag), latex_equiv, text)

        # Escape basic LaTeX special characters
        special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "^": r"\^{}"
        }

        # Replace only if the character is outside LaTeX commands
        for char, escaped in special_chars.items():
            text = text.replace(char, escaped)

        return text

    def append_link(self, entry, reference, *args):
        return f"{entry} \\cite{{{reference.key}}}"


class MarkdownFormatter(OutputFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        return f"{formatted_author}"

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)

    def format_final_entry(self, text, reference, *args, **kwargs):
        """
        Converts HTML-style formatting tags to Markdown equivalents.
        Removes unsupported HTML tags.
        """
        replacements = {
            r"<i>": r"*",       # <i> → *
            r"</i>": r"*",      # </i> → *
            r"<b>": r"**",      # <b> → **
            r"</b>": r"**",     # </b> → **
            r"<u>": r"",        # <u> (unsupported in Markdown) → removed
            r"</u>": r""        # </u> (unsupported in Markdown) → removed
        }

        # Perform replacements
        for html_tag, markdown_equiv in replacements.items():
            text = re.sub(html_tag, markdown_equiv, text)

        return text

    def append_link(self, entry, reference, *args):
        """
        Appends a Markdown-style link to the given entry.
        If "reference" is in args, the full DOI/URL is displayed as text.
        Otherwise, a simple "[>]" clickable link is used.
        """
        if not reference.link_doi:
            return entry  # No link to append

        if "reference" in args:
            markdown_link = f"[{reference.link_doi}]({reference.link_doi})"
        else:
            markdown_link = f"[>](<{reference.link_doi}>)"

        return f"{entry} {markdown_link}"



class RtfFormatter(OutputFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        return f"{formatted_author}"

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)

    def format_final_entry(self, text, reference, *args, **kwargs):
        """
        Replaces specific HTML-style formatting tags with RTF equivalents.
        Ensures proper escaping of backslashes.
        """
        replacements = {
            r"<i>": r"\\i ",      # Start italic (escaped backslash)
            r"</i>": r"\\i0 ",    # End italic
            r"<b>": r"\\b ",      # Start bold
            r"</b>": r"\\b0 ",    # End bold
            r"<u>": r"\\ul ",     # Start underline
            r"</u>": r"\\ul0 "    # End underline
        }

        # Apply replacements
        for html_tag, rtf_equiv in replacements.items():
            text = re.sub(html_tag, rtf_equiv, text)  # Proper escaping fixes error

        return r"{\rtf1\ansi " + text + "}"

    def append_link(self, entry, reference, *args):
        """
        Converts a reference link into RTF format.
        If 'reference' is in args, the full URL is displayed.
        Otherwise, a simple clickable link is used.
        """
        if not reference.link_doi:
            return entry  # No link to append

        if "reference" in args:
            rtf_link = (
                r"{\field{\*\fldinst HYPERLINK \"" + reference.link_doi + r"\"}"
                r"{\fldrslt " + reference.link_doi + r"}}"
            )
        else:
            rtf_link = (
                r"{\field{\*\fldinst HYPERLINK \"" + reference.link_doi + r"\"}"
                r"{\fldrslt [>]}}"
            )
        # NOTE: append_link in RtfFormatter sets it right, but copy method in MultiClipboard does not process it correctly
        print("RTF Linking set correctly, but not processed correctly in MultiClipboard", file=sys.stderr)
        return f"{entry} {rtf_link}"

class OutputFormatterFactory:
    _formatters = {}

    @classmethod
    def register_formatter(cls, key, formatter_cls):
        """Registers a new formatter class under a string key."""
        cls._formatters[key.lower()] = formatter_cls

    @classmethod
    def get_formatter(cls, key):
        """Returns the formatter instance corresponding to the given key."""
        formatter_cls = cls._formatters.get(key.lower())
        if not formatter_cls:
            raise ValueError(f"Unknown formatter: {key}")
        return formatter_cls()

OutputFormatterFactory.register_formatter("plain", PlainFormatter)
OutputFormatterFactory.register_formatter("Plain", PlainFormatter)
OutputFormatterFactory.register_formatter("html", HtmlFormatter)
OutputFormatterFactory.register_formatter("HTML", HtmlFormatter)
OutputFormatterFactory.register_formatter("html_css", HtmlCssFormatter)
OutputFormatterFactory.register_formatter("HTML+CSS", HtmlCssFormatter)
OutputFormatterFactory.register_formatter("latex", LatexFormatter)
OutputFormatterFactory.register_formatter("LaTeX", LatexFormatter)
OutputFormatterFactory.register_formatter("markdown", MarkdownFormatter)
OutputFormatterFactory.register_formatter("Markdown", MarkdownFormatter)
OutputFormatterFactory.register_formatter("richtext", RtfFormatter)
OutputFormatterFactory.register_formatter("RichText", RtfFormatter)
OutputFormatterFactory.register_formatter("--format--", None)

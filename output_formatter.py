from abc import ABC, abstractmethod

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

    def format_final_entry(self, entry, *args, **kwargs):
        return entry


class PlainFormatter(OutputFormatter):
    pass


class HtmlFormatter(OutputFormatter):
    pass


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

    def format_final_entry(self, entry, *args, **kwargs):
        id = kwargs.get("id", '')
        if id:
            return f"<div id='{id}>{entry}</div>"
        return entry

class LatexFormatter(OutputFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        return f"\\textbf{{{formatted_author}}}"

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)


class MarkdownFormatter(OutputFormatter):
    def format_author(self, author, *args, **kwargs):
        formatted_author = author._format(*args, **kwargs)
        return f"**{formatted_author}**"

    def format_authors(self, author_list, *args, **kwargs):
        return author_list._format(*args, **kwargs)


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
OutputFormatterFactory.register_formatter("--format--", None)

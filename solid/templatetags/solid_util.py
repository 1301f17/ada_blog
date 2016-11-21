from django import template
from django.db import models
from django.template.defaultfilters import truncatewords_html

from mezzanine.core.fields import RichTextField, OrderField
from mezzanine.utils.html import TagCloser


register = template.Library()


@register.filter(name='long_description_from_content')
def long_description_from_content(item, nlines="5"):
    """
    A multi-line version of this:
    https://github.com/stephenmcd/mezzanine/blob/7a33f1a41973a0fc6c54d5d89233c10307d39503/mezzanine/core/models.py#L151
    Returns the first n blocks or sentences of the first content-like
    field.
    """
    nlines = int(nlines)
    max_description_length = 100*nlines

    description = ""

    # Use the first RichTextField, or TextField if none found.
    for field_type in (RichTextField, models.TextField):
        if not description:
            for field in item._meta.fields:
                if (isinstance(field, field_type) and
                        field.name != "description"):
                    description = getattr(item, field.name)
                    if description:
                        from mezzanine.core.templatetags.mezzanine_tags \
                                                import richtext_filters
                        description = richtext_filters(description)
                        break

    # Fall back to the title if description couldn't be determined.
    if not description:
        description = str(item)

    # Find the block of text containing the first `nlines` endings.
    endings = ("</p>", "<br />", "<br/>", "<br>", "</ul>",
            "\n", ". ", "! ", "? ")

    search_start_position = 0
    n_endings_found = 0
    last_search_offset = 0
    done_searching = False

    for ending in endings:
        while not done_searching and last_search_offset > -1 and search_start_position < max_description_length:
            last_search_offset = description.lower().find(ending, search_start_position)
            if last_search_offset > -1:
                # Found an ending
                # Advance the current offset
                search_start_position = last_search_offset + len(ending)
                n_endings_found += 1
            else:
                # Nothing was found, check the next ending
                last_search_offset = 0
                break

            if n_endings_found >= nlines:
                # Found the requested number of lines
                description = TagCloser(description[:search_start_position]).html
                done = True
                break

    if not done_searching:
        # Didn't find the requested number of lines, either because text was too short or too long
        # Either way, truncate to max description length
        description = truncatewords_html(description, max_description_length)

    try:
        description = unicode(description)
    except NameError:
        pass  # Python 3.

    return description
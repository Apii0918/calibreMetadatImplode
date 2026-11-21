__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

TEMPLATE_REF_URL = 'https://manual.calibre-ebook.com/generated/en/template_ref.html'
READING_PROGRESS_URL = 'https://manual.calibre-ebook.com/generated/en/template_ref.html#reading-progress'
GET_NOTE_URL = 'https://manual.calibre-ebook.com/generated/en/template_ref.html#get-note'
URLS_FROM_IDENTIFIERS_URL = 'https://manual.calibre-ebook.com/generated/en/template_ref.html#urls-from-identifiers'
MAKE_URL_URL = 'https://manual.calibre-ebook.com/generated/en/template_ref.html#make-url'


def build_general_help_links(_):
    return [
        (_('Template reference'), TEMPLATE_REF_URL),
        (_('calibre 9.5: reading_progress()'), READING_PROGRESS_URL),
    ]


def build_helper_group_definitions(_):
    return [
        {
            'key': 'viewer',
            'title': _('Calibre Viewer'),
            'section': 'reading_workflows',
            'section_title': _('Reading workflows'),
            'summary': _('Columns that integrate with {0} functions and viewer-derived data such as annotations, progress, and last viewed timestamps.').format('Calibre Viewer'),
            'help_links': [(_('reading_progress() docs'), READING_PROGRESS_URL)],
        },
        {
            'key': 'tracker',
            'title': _('Reading Tracker'),
            'section': 'reading_workflows',
            'section_title': _('Reading workflows'),
            'summary': _('Columns for manual reading logs, start/finish dates, progress, ratings, and review notes.'),
        },
        {
            'key': 'goal',
            'title': _('Reading Goal'),
            'section': 'reading_workflows',
            'section_title': _('Reading workflows'),
            'summary': _('Columns for lightweight reading-goal workflows such as progress, status date, page totals, and genres.'),
        },
        {
            'key': 'review',
            'title': _('Personal Review'),
            'section': 'reading_workflows',
            'section_title': _('Reading workflows'),
            'summary': _('Columns for writing your own book reviews directly in calibre — a long-text review, a personal rating, the date you reviewed it, a recommend flag, and free-form review tags.'),
        },
        {
            'key': 'research',
            'title': _('Author & Web Research'),
            'section': 'research_web',
            'section_title': _('Research & web'),
            'summary': _('Columns for author notes, Goodreads identifiers, and web-search helpers that connect metadata to external research workflows.'),
            'help_links': [
                (_('get_note() docs'), GET_NOTE_URL),
                (_('urls_from_identifiers() docs'), URLS_FROM_IDENTIFIERS_URL),
                (_('make_url() docs'), MAKE_URL_URL),
            ],
        },
        {
            'key': 'kobo_utilities',
            'title': 'Kobo Utilities',
            'section': 'device_sync',
            'section_title': _('Device sync'),
            'summary': _('Columns used by {0} to store device-side reading position, dates, ratings, and time estimates.').format('Kobo Utilities'),
        },
        {
            'key': 'general_counts',
            'title': _('General Counts'),
            'section': 'statistics_counts',
            'section_title': _('Statistics & counts'),
            'summary': _('Reusable count columns such as tag, publisher, author, and similar library statistics.'),
        },
        {
            'key': 'count_pages',
            'title': 'Count Pages',
            'section': 'statistics_counts',
            'section_title': _('Statistics & counts'),
            'summary': _('Columns used by {0} for pages, words, and readability metrics.').format('Count Pages'),
        },
        {
            'key': 'blp',
            'title': 'Book List Plus',
            'section': 'cover_display',
            'section_title': _('Cover display'),
            'summary': _('Columns designed for {0} cover grid layouts — composite columns that combine pages, file sizes, annotation counts, and other metadata into compact display fields.').format('Book List Plus'),
        },
        {
            'key': 'cover_size',
            'title': 'Cover Size Checker',
            'section': 'cover_display',
            'section_title': _('Cover display'),
            'summary': _('Columns used by {0} to store cover image dimensions and a small-cover flag.').format('Cover Size Checker'),
        },
    ]


def build_quick_create_presets(_):
    return {
        'builtin': {
            'isbn': {
                'lookup_name': '#isbn', 'heading': 'ISBN', 'datatype': 'composite', 'is_multiple': False,
                'display': {'composite_template': '{identifiers:select(isbn)}', 'composite_sort': 'text', 'make_category': False, 'contains_html': False, 'composite_show_in_comments': False, 'composite_store_template_value_in_opf': True, 'use_decorations': False, 'description': ''},
                'link_text': 'ISBN', 'menu_text': 'ISBN'
            },
            'formats': {
                'lookup_name': '#formats', 'heading': _('Formats'), 'datatype': 'composite', 'is_multiple': False,
                'display': {'composite_template': "{:'re(approximate_formats(), ',', ', ')'}", 'composite_sort': 'text', 'make_category': False, 'contains_html': False, 'composite_show_in_comments': False, 'composite_store_template_value_in_opf': True, 'use_decorations': False, 'description': ''},
                'link_text': _('Formats'), 'menu_text': _('Formats')
            },
            'yesno': {
                'lookup_name': '#yesno', 'heading': _('Yes/No'), 'datatype': 'bool', 'is_multiple': False,
                'display': {'bools_show_text': False, 'bools_show_icons': True, 'description': ''},
                'link_text': _('Yes/No'), 'menu_text': _('Yes/No')
            },
            'tags': {
                'lookup_name': '#tags', 'heading': _('My Tags'), 'datatype': 'text', 'is_multiple': True,
                'display': {'is_names': False, 'description': ''},
                'link_text': _('Tags'), 'menu_text': _('Tags')
            },
            'series': {
                'lookup_name': '#series', 'heading': _('My Series'), 'datatype': 'series', 'is_multiple': False,
                'display': {'description': ''},
                'link_text': _('Series'), 'menu_text': _('Series')
            },
            'rating': {
                'lookup_name': '#rating', 'heading': _('My Rating'), 'datatype': 'rating', 'is_multiple': False,
                'display': {'allow_half_stars': False, 'description': ''},
                'link_text': _('Rating'), 'menu_text': _('Rating')
            },
            'people': {
                'lookup_name': '#people', 'heading': _('People'), 'datatype': 'text', 'is_multiple': True,
                'display': {'is_names': True, 'description': ''},
                'link_text': _('Names'), 'menu_text': _('Names')
            },
            'text': {
                'lookup_name': '#text', 'heading': _('My Title'), 'datatype': 'comments', 'is_multiple': False,
                'display': {'heading_position': 'side', 'interpret_as': 'short-text', 'description': ''},
                'link_text': _('Short text'), 'menu_text': _('Short text')
            },
            'read_progress': {
                'lookup_name': '#read_progress', 'heading': _('Read progress'), 'datatype': 'composite', 'is_multiple': False,
                'display': {'composite_template': '{id:reading_progress()}', 'composite_sort': 'number', 'make_category': False, 'contains_html': False, 'composite_show_in_comments': False, 'composite_store_template_value_in_opf': False, 'use_decorations': False, 'description': _('To customize this, read the help for the reading_progress() template function in the calibre User Manual')},
                'link_text': _('Read progress'), 'menu_text': _('Read progress'),
                'help_links': [(_('reading_progress() docs'), READING_PROGRESS_URL)],
            },
        },
        'tracker': {
            'tracked': {
                'lookup_name': '#tracked', 'heading': _('Tracked'), 'datatype': 'bool', 'is_multiple': False,
                'display': {'bools_show_text': False, 'bools_show_icons': True, 'description': _('Mark which books appear in the Reading Tracker (set to Yes)')},
                'menu_text': _('Tracked (#tracked)')
            },
            'status': {
                'lookup_name': '#status', 'heading': _('Status'), 'datatype': 'text', 'is_multiple': False,
                'display': {'use_decorations': False, 'description': _('Reading status: Reading, Finished, TBR, Paused, or DNF')},
                'menu_text': _('Status (#status)')
            },
            'start_date': {
                'lookup_name': '#start_date', 'heading': _('Start Date'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': None, 'description': _('The date you started reading')},
                'menu_text': _('Start Date (#start_date)')
            },
            'finish_date': {
                'lookup_name': '#finish_date', 'heading': _('Finish Date'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': None, 'description': _('The date you finished reading')},
                'menu_text': _('Finish Date (#finish_date)')
            },
            'pages': {
                'lookup_name': '#pp', 'heading': _('Pages'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': None, 'description': _('Total page count of the book')},
                'menu_text': _('Pages (#pp)')
            },
            'my_review': {
                'lookup_name': '#my_review', 'heading': _('My Review'), 'datatype': 'comments', 'is_multiple': False,
                'display': {'heading_position': 'hide', 'interpret_as': 'long-text', 'description': _('Your personal review or notes')},
                'menu_text': _('My Review (#my_review)')
            },
            'type': {
                'lookup_name': '#type', 'heading': _('Type'), 'datatype': 'text', 'is_multiple': False,
                'display': {'use_decorations': False, 'description': _('Format type: ebook, audio, or print')},
                'menu_text': _('Type (#type)')
            },
            'percentage': {
                'lookup_name': '#percentage', 'heading': _('% Read'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': None, 'description': _('Percentage of the book you have read (0-100)')},
                'menu_text': _('% Read (#percentage)')
            },
            'my_rating': {
                'lookup_name': '#my_rating', 'heading': _('My Rating'), 'datatype': 'float', 'is_multiple': False,
                'display': {'number_format': '{0:.1f}', 'decimals': 1, 'description': _('Your personal rating on a 0-5 scale (supports half stars)')},
                'menu_text': _('My Rating (#my_rating)')
            },
        },
        'goal': {
            'percentage': {
                'lookup_name': '#percentage', 'heading': _('% Read'), 'datatype': 'float', 'is_multiple': False,
                'display': {'number_format': '{:.0f}%', 'decimals': 2, 'description': _('Reading progress')},
                'menu_text': _('% Read (#percentage)')
            },
            'read_date': {
                'lookup_name': '#read_date', 'heading': _('Status date'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': None, 'description': _('Reading progress date')},
                'menu_text': _('Status date (#read_date)')
            },
            'pages': {
                'lookup_name': '#pages', 'heading': _('Pages'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': None, 'description': _('Page count')},
                'menu_text': _('Pages (#pages)')
            },
            'genres': {
                'lookup_name': '#genres', 'heading': _('Genres'), 'datatype': 'text', 'is_multiple': False,
                'display': {'use_decorations': False, 'description': _('Book genre')},
                'menu_text': _('Genres (#genres)')
            },
        },
        'review': {
            'review': {
                'lookup_name': '#review', 'heading': _('My Review'), 'datatype': 'comments', 'is_multiple': False,
                'display': {'heading_position': 'above', 'interpret_as': 'long-text', 'description': _('Your personal written review of the book.')},
                'menu_text': _('My Review (#review)')
            },
            'review_rating': {
                'lookup_name': '#review_rating', 'heading': _('My Rating'), 'datatype': 'rating', 'is_multiple': False,
                'display': {'allow_half_stars': True, 'description': _('Your personal star rating (supports half stars).')},
                'menu_text': _('My Rating (#review_rating)')
            },
            'review_date': {
                'lookup_name': '#review_date', 'heading': _('Reviewed On'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': None, 'description': _('The date you wrote the review.')},
                'menu_text': _('Reviewed On (#review_date)')
            },
            'recommend': {
                'lookup_name': '#recommend', 'heading': _('Recommend'), 'datatype': 'bool', 'is_multiple': False,
                'display': {'bools_show_text': False, 'bools_show_icons': True, 'description': _('Flag whether you would recommend this book.')},
                'menu_text': _('Recommend (#recommend)')
            },
            'review_tags': {
                'lookup_name': '#review_tags', 'heading': _('Review Tags'), 'datatype': 'text', 'is_multiple': True,
                'display': {'is_names': False, 'description': _('Free-form tags for your review, e.g. favourite, re-read, disappointing.')},
                'menu_text': _('Review Tags (#review_tags)')
            },
        },
        'viewer': {
            'annotation_count': {
                'lookup_name': '#ac', 'heading': _('Annotation Count'), 'datatype': 'composite', 'is_multiple': False,
                'display': {'composite_template': 'program: annotation_count()', 'composite_sort': 'number', 'make_category': False, 'contains_html': False, 'composite_show_in_comments': False, 'composite_store_template_value_in_opf': True, 'use_decorations': False, 'description': _('Calibre Viewer annotation count.')},
                'menu_text': _('Annotation Count (#ac)')
            },
            'read_progress': {
                'lookup_name': '#read_progress', 'heading': _('Read progress'), 'datatype': 'composite', 'is_multiple': False,
                'display': {'composite_template': '{id:reading_progress()}', 'composite_sort': 'number', 'make_category': False, 'contains_html': False, 'composite_show_in_comments': False, 'composite_store_template_value_in_opf': False, 'use_decorations': False, 'description': _('Viewer read progress using calibre\'s reading_progress() template function.')},
                'menu_text': _('Read progress (#read_progress)'),
                'help_links': [(_('reading_progress() docs'), READING_PROGRESS_URL)],
            },
            'last_viewed': {
                'lookup_name': '#last_viewed', 'heading': _('Last Viewed'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': 'dd-MM-yyyy hh:mm', 'description': _('Timestamp for when the book was last viewed in calibre.')},
                'menu_text': _('Last Viewed (#last_viewed)'),
                'info_text': _('Requires the Job Spy plugin to be installed and configured so this timestamp is captured and updated.'),
            },
        },
        'research': {
            'author_sort': {
                'lookup_name': '#as', 'heading': _('Author sort'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': '{author_sort}',
                    'composite_sort': 'text',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Author sort'),
                },
                'description': _('Author sort'),
                'menu_text': _('Author sort (#as)'),
            },
            'bio': {
                'lookup_name': '#bio', 'heading': _('Bio'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': "program: get_note('authors', $authors, '')",
                    'composite_sort': 'text',
                    'make_category': False,
                    'contains_html': True,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('GR Author Notes plugin - Author Bio column'),
                },
                'description': _('GR Author Notes plugin - Author Bio column'),
                'menu_text': _('Bio (#bio)'),
                'help_links': [(_('get_note() docs'), GET_NOTE_URL)],
            },
            'gr': {
                'lookup_name': '#gr', 'heading': _('GR'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': "program: out = ' 🔗'; out = strcat(out,\n    gr_id = select($identifiers, 'goodreads');\n    if gr_id then\n        l = urls_from_identifiers( 'goodreads:' & gr_id, '');\n        l = re(l, '>goodreads<', '>' & gr_id & '<')\n    else\n        l = ''\n    fi); out",
                    'composite_sort': 'text',
                    'make_category': False,
                    'contains_html': True,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Dedicated identifier for Goodreads'),
                },
                'description': _('Dedicated identifier for Goodreads'),
                'menu_text': _('GR (#gr)'),
                'help_links': [(_('urls_from_identifiers() docs'), URLS_FROM_IDENTIFIERS_URL)],
            },
            'grrating': {
                'lookup_name': '#grrating', 'heading': _('GR Rating'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': '{identifiers:select(grrating)}',
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Goodreads Plugin rating column'),
                },
                'description': _('Goodreads Plugin rating column'),
                'menu_text': _('GR rating (#grrating)'),
            },
            'grvotes': {
                'lookup_name': '#grvotes', 'heading': _('GR Votes'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': '{identifiers:select(grvotes)}',
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Goodreads Plugin vote-count column'),
                },
                'description': _('Goodreads Plugin vote-count column'),
                'menu_text': _('GR votes (#grvotes)'),
            },
            'phind': {
                'lookup_name': '#phind', 'heading': _('Phind'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': '{title} by {author} Phind',
                    'web_search_template': "program: make_url('https://phind.com/search', 'q', $title  & ' by ' & $author)",
                    'composite_sort': 'text',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Title by author Phind'),
                },
                'description': _('Title by author Phind'),
                'menu_text': _('Phind (#phind)'),
                'help_links': [(_('make_url() docs'), MAKE_URL_URL)],
            },
        },
        'kobo_utilities': {
            'current_reading_location': {
                'lookup_name': '#kobo_reading_location', 'heading': _('Kobo Reading Location'), 'datatype': 'text', 'is_multiple': False,
                'display': {'use_decorations': False, 'description': _('Kobo Utilities: current reading location link. Recommended text column.')},
                'menu_text': _('Current Reading Location (#kobo_reading_location)')
            },
            'percent_read': {
                'lookup_name': '#kobo_percent_read', 'heading': _('Kobo % Read'), 'datatype': 'float', 'is_multiple': False,
                'display': {'number_format': '{0:.1f}', 'decimals': 1, 'description': _('Kobo Utilities: current percentage read.')},
                'menu_text': _('Percent Read (#kobo_percent_read)')
            },
            'rating': {
                'lookup_name': '#kobo_rating', 'heading': _('Kobo Rating'), 'datatype': 'rating', 'is_multiple': False,
                'display': {'allow_half_stars': False, 'description': _('Kobo Utilities: device rating.')},
                'menu_text': _('Rating (#kobo_rating)')
            },
            'last_read_timestamp': {
                'lookup_name': '#kobo_last_read', 'heading': _('Kobo Last Read'), 'datatype': 'datetime', 'is_multiple': False,
                'display': {'date_format': None, 'description': _('Kobo Utilities: last read timestamp.')},
                'menu_text': _('Last Read Timestamp (#kobo_last_read)')
            },
            'time_spent_reading': {
                'lookup_name': '#kobo_time_spent', 'heading': _('Kobo Time Spent'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': None, 'description': _('Kobo Utilities: time spent reading, in seconds.')},
                'menu_text': _('Time Spent Reading (#kobo_time_spent)')
            },
            'rest_of_book_estimate': {
                'lookup_name': '#kobo_rest_estimate', 'heading': _('Kobo Rest Estimate'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': None, 'description': _('Kobo Utilities: estimated time left to finish, in seconds.')},
                'menu_text': _('Rest of Book Estimate (#kobo_rest_estimate)')
            },
        },
        'general_counts': {
            'tag_count': {
                'lookup_name': '#tn', 'heading': _('Tag N'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': "program: list_count_field('tags')",
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Tag count test'),
                },
                'description': _('Tag count test'),
                'menu_text': _('Tag N (#tn)')
            },
            'author_count': {
                'lookup_name': '#an', 'heading': _('Author N'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': "program: list_count_field('authors')",
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Number of Authors'),
                },
                'description': _('Number of Authors'),
                'menu_text': _('Author N (#an)')
            },
            'publisher_count': {
                'lookup_name': '#pc', 'heading': _('Publisher count'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': (
                        'python:\n'
                        'def evaluate(book, context):\n'
                        '\tdb = context.db.new_api\n'
                        '\tpub_id = db.field_ids_for(\'publisher\', book.id)\n'
                        '\tif not pub_id:\n'
                        '\t\treturn \'0\'\n'
                        '\tpub_id = pub_id[0]\n'
                        '\tcounts = db.get_usage_count_by_id(\'publisher\')\n'
                        '\treturn str(counts[pub_id])'
                    ),
                    'composite_sort': 'number',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': False,
                    'use_decorations': False,
                    'description': _('Number of books by publisher'),
                },
                'description': _('Number of books by publisher'),
                'menu_text': _('Publisher count (#pc)')
            },
        },
        'count_pages': {
            'pages': {
                'lookup_name': '#pp', 'heading': _('Pages'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': '{0:,d}', 'description': _('Count Pages: page count.')},
                'menu_text': _('Pages (#pp)')
            },
            'words': {
                'lookup_name': '#words', 'heading': _('Words'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': '{0:,d}', 'description': _('Count Pages: word count.')},
                'menu_text': _('Words (#words)')
            },
            'gfog': {
                'lookup_name': '#gfog', 'heading': _('Gunning Fog'), 'datatype': 'float', 'is_multiple': False,
                'display': {'number_format': '{0:.1f}', 'decimals': 1, 'description': _('Count Pages: Gunning Fog readability index.')},
                'menu_text': _('Gunning Fog (#gfog)')
            },
        },
        'blp': {
            'cover_grid_second': {
                'lookup_name': '#blp', 'heading': _('BLP'), 'datatype': 'composite', 'is_multiple': False,
                'display': {
                    'composite_template': (
                        'program: def do_field(field_name, icon):\n'
                        '    if field(field_name) then icon & field(field_name) else \'\' fi\n'
                        'fed;\n'
                        '\n'
                        'max_size = 0;\n'
                        'fmts = formats_sizes();\n'
                        'for f in fmts:\n'
                        '    s = sublist(f, 1, 2, \':\');\n'
                        '    if s ># max_size then max_size = s fi\n'
                        'rof;\n'
                        'size_part = if max_size ># 0 then strcat(\'📦\', human_readable(max_size)) else \'\' fi;\n'
                        '\n'
                        'strcat(\n'
                        '  do_field(\'pages\', \'📖\'),\n'
                        '  \' \',\n'
                        '  size_part,\n'
                        '  \' \',\n'
                        '  do_field(\'#ac\', \'🟨\')\n'
                        ')'
                    ),
                    'composite_sort': 'text',
                    'make_category': False,
                    'contains_html': False,
                    'composite_show_in_comments': False,
                    'composite_store_template_value_in_opf': True,
                    'use_decorations': False,
                    'description': _('BLP cover grid second field: pages, file size, and annotation count.'),
                },
                'description': _('BLP cover grid second field: pages, file size, and annotation count.'),
                'menu_text': _('BLP cover grid second field (#blp)'),
            },
        },
        'cover_size': {
            'cover_width': {
                'lookup_name': '#cover_width', 'heading': _('Cover Width'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': '{0:,d}', 'description': _('Cover Size Checker: cover image width in pixels.')},
                'menu_text': _('Cover Width (#cover_width)')
            },
            'cover_height': {
                'lookup_name': '#cover_height', 'heading': _('Cover Height'), 'datatype': 'int', 'is_multiple': False,
                'display': {'number_format': '{0:,d}', 'description': _('Cover Size Checker: cover image height in pixels.')},
                'menu_text': _('Cover Height (#cover_height)')
            },
            'cover_small': {
                'lookup_name': '#cover_small', 'heading': _('Cover Small'), 'datatype': 'bool', 'is_multiple': False,
                'display': {'bools_show_text': False, 'bools_show_icons': True, 'description': _('Cover Size Checker: flagged Yes when cover width is below 450 px.')},
                'menu_text': _('Cover Small (#cover_small)')
            },
        },
    }

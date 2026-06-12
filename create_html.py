#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "html5lib"]
# ///
"""Create HTML version of the textbook (run with `uv run create_html.py`).

This is adapted from the build system of the sister project ../logic3.
The pipeline is:

  1. copy the .tex sources into a tmp/ directory, lightly rewriting constructs
     that make4ht/tex4ht can't handle (custom macros, breakable tcolorboxes, …);
  2. run make4ht to turn the LaTeX into one HTML file per chapter, with math
     handed to MathJax and TikZ pictures rendered to SVG;
  3. post-process the HTML: rename the files, embed them in html_template.html,
     tidy up the tcolorboxes and lists, and build index.html / toc.html.
"""

import os
import re
import shutil
import subprocess
import argparse
import datetime
from bs4 import BeautifulSoup
from html5lib import HTMLParser, constants

tmp_path = "tmp"
html_path = "html"

# Name of the LaTeX master file and the CSS file linked from the template.
main_tex = "bdrc.tex"
css_file = "bdrc.css"

tex4ht_config = r"""
\Preamble{xhtml}
\Configure{tableofcontents*}{chapter,section,subsection}
\begin{document}
\EndPreamble
"""


MATHJAX_VERSION = "4.1.1"
MATHJAX_SCRIPT = f"html/mathjax/tex-chtml-nofont.js"
STIX2_CHTML = f"html/mathjax-fonts/mathjax-stix2-font/chtml.js"


def ensure_mathjax():
    """Download MathJax and STIX2 font files if not already present."""
    if os.path.exists(MATHJAX_SCRIPT) and os.path.exists(STIX2_CHTML):
        return
    import tempfile
    print("Installing MathJax and STIX2 font...")
    os.makedirs("html/mathjax", exist_ok=True)
    os.makedirs("html/mathjax-fonts/mathjax-stix2-font", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        v = MATHJAX_VERSION
        # MathJax — full package (extensions loaded dynamically need to be present)
        subprocess.run(["npm", "pack", f"mathjax@{v}"], cwd=tmp, check=True,
                       capture_output=True)
        subprocess.run(["tar", "-xzf", f"mathjax-{v}.tgz", "--strip-components=1",
                        "-C", os.path.abspath("html/mathjax")], cwd=tmp, check=True,
                       capture_output=True)
        # STIX2 font package (chtml files only)
        subprocess.run(["npm", "pack", f"@mathjax/mathjax-stix2-font@{v}"],
                       cwd=tmp, check=True, capture_output=True)
        subprocess.run(["tar", "-xzf", f"mathjax-mathjax-stix2-font-{v}.tgz",
                        "--strip-components=1",
                        "-C", os.path.abspath("html/mathjax-fonts/mathjax-stix2-font"),
                        "--wildcards", "package/chtml*"],
                       cwd=tmp, check=True, capture_output=True)
    print("✓ MathJax installed.")


def main():
    """Create HTML version of textbook."""
    argparser = argparse.ArgumentParser(description="Create HTML version")
    argparser.add_argument('-f', '--fake', action='store_true', help="Use previous make4ht output")
    argparser.add_argument('-v', '--verbose', action='store_true', help="Verbose output")
    args = argparser.parse_args()

    ensure_mathjax()

    if not args.fake:
        prepare_paths()
        prepare_tex()
        make4ht(verbose=args.verbose)
        restore_css()
    save_or_restore_make4ht_output(restore=args.fake)

    rename_html_files()
    fix_html()
    create_index()
    check_links()


def prepare_paths():
    """Ensure tmp and html directories exist and tmp is empty."""
    try:
        shutil.rmtree(tmp_path)
    except FileNotFoundError:
        pass
    os.mkdir(tmp_path)
    if not os.path.exists(html_path):
        os.mkdir(html_path)
    # Preserve the hand-maintained CSS, which make4ht would otherwise overwrite:
    if os.path.exists(html_path + '/' + css_file):
        print(f"Renaming {css_file} to _{css_file}")
        shutil.copyfile(html_path + '/' + css_file, html_path + '/_' + css_file)
    # create tex4ht configuration file:
    write_file(tmp_path + "/mytex4ht.cfg", tex4ht_config.strip())


def restore_css():
    """Restore customized CSS file that's overwritten by make4ht."""
    if os.path.exists(html_path + '/_' + css_file):
        shutil.move(html_path + '/_' + css_file, html_path + '/' + css_file)


def prepare_tex():
    """Prepare the LaTeX files for processing."""
    shutil.copy(main_tex, tmp_path + '/' + main_tex)
    for chapter in tex_files():
        prep_chapter(chapter)
    prep_bdrc_cls()
    shutil.copy('doclicense-CC-by-nc-sa.pdf', tmp_path)
    shutil.copy('doclicense-CC-by-nc-sa.svg', tmp_path + '/doclicense-CC-by-nc-sa-88x31.svg')
    # Copy figures directory if it exists:
    if os.path.exists('figures'):
        shutil.copytree('figures', tmp_path + '/figures', dirs_exist_ok=True)


def tex_files():
    """Return list of chapter files (plus the title page)."""
    pattern = re.compile(r'^\d\d-[^.]+\.tex$')
    chapters = [f for f in os.listdir('.') if pattern.match(f)]
    chapters.append('title.tex')
    return chapters


def html_files():
    """Return list of HTML files."""
    return [f for f in os.listdir(html_path) if f.endswith('.html')]


def prep_bdrc_cls():
    """Prepare bdrc.cls for conversion to HTML.

    The tcolorbox environments (example, exercise, essay, …) are defined in the
    class file. Their `breakable` / `enhanced jigsaw` options confuse tex4ht, so
    we disable them — in HTML there are no pages to break across anyway.
    """
    cls = read_file("bdrc.cls")
    cls = re.sub(r'(?m)^\s*breakable,', '%breakable,', cls)
    cls = re.sub(r'(?m)^\s*enhanced jigsaw,', '%enhanced jigsaw,', cls)
    write_file(tmp_path + "/bdrc.cls", cls)


def prep_chapter(texfile):
    """Edit a LaTeX chapter for conversion to HTML."""
    tex = read_file(texfile)
    tex = remove_noindent(tex)
    tex = fix_custom_commands(tex)
    tex = fix_math_line_spacing(tex)
    tex = escape_labeled_items(tex)
    tex = escape_intext_links(tex)
    tex = mark_decision_tables(tex)
    write_file(tmp_path + "/" + texfile, tex)


def remove_noindent(tex):
    r"""Remove \noindent commands that prevent rendering text as p."""
    # Replace with a space to avoid joining adjacent words.
    return re.sub(r'\\noindent\s*%?', ' ', tex)


_MATH_REGION = re.compile(
    r'\\\(.*?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|\$.*?\$|'
    r'\\begin\{(equation\*?|align\*?|flalign\*?|gather\*?|multline\*?|eqnarray\*?)\}'
    r'.*?\\end\{\1\}',
    re.DOTALL,
)

# Same, but for HTML output, where tex4ht may insert spaces in \begin {align*}.
_HTML_MATH_REGION = re.compile(
    r'\\\(.*?\\\)|\\\[.*?\\\]|'
    r'\\begin\s*\{(equation\*?|align\*?|flalign\*?|gather\*?|multline\*?|eqnarray\*?)\}'
    r'.*?\\end\s*\{\1\}',
    re.DOTALL,
)


def sub_outside_math(pattern, replacement, tex):
    """Apply re.sub only to non-math segments of tex."""
    out = []
    last = 0
    for m in _MATH_REGION.finditer(tex):
        out.append(re.sub(pattern, replacement, tex[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(re.sub(pattern, replacement, tex[last:]))
    return ''.join(out)


def fix_custom_commands(tex):
    r"""Fix custom commands that make4ht/MathJax don't understand.

    Most of the book's math macros (\Cr, \U, \pref, \bet, \boxright, …) are
    declared as MathJax macros in html_template.html, so they pass through
    untouched. The \celsius / \fahrenheit macros, however, are used in text
    mode, where MathJax never sees them — so we replace them with literal
    degree strings outside of math.
    """
    tex = sub_outside_math(r'\\celsius(?![a-zA-Z])', r'°C', tex)
    tex = sub_outside_math(r'\\fahrenheit(?![a-zA-Z])', r'°F', tex)
    # enumitem's inline enumerate* renders badly in tex4ht (the counter stays at
    # 0 and the custom \item[...] labels are dropped). Every such list here uses
    # custom labels, so render them as itemize and let escape_labeled_items /
    # fix_item_labels preserve the labels.
    tex = re.sub(r'\\begin\{enumerate\*\}', r'\\begin{itemize}', tex)
    tex = re.sub(r'\\end\{enumerate\*\}', r'\\end{itemize}', tex)
    return tex


def fix_math_line_spacing(tex):
    r"""Add extra row spacing in display math environments for HTML rendering.

    Replaces \\ (row break) with \\[0.5em] so MathJax row spacing better matches
    the surrounding text line height. Skips \\ that already carry explicit
    spacing (\\[...]) or a star (\\*).
    """
    def add_spacing(m):
        return re.sub(r'\\\\(?![\[*])', r'\\\\[0.5em]', m.group(0))
    display = re.compile(
        r'\\\[.*?\\\]|\$\$.*?\$\$|'
        r'\\begin\{(equation\*?|align\*?|flalign\*?|gather\*?|multline\*?|eqnarray\*?)\}'
        r'.*?\\end\{\1\}',
        re.DOTALL,
    )
    return display.sub(add_spacing, tex)


def escape_labeled_items(tex):
    r"""Escape labeled \item to preserve the label.

    '\item[(*)] text' would be turned into a bulleted list item by make4ht,
    losing the label. We mark the label so we can restore it later.
    """
    tex = re.sub(r'\\item\[(.+?)\]', r'\\item[\1] ITEMLABEL\1ENDITEMLABEL', tex)
    return tex


def mark_decision_tables(tex):
    r"""Mark the shaded parts of decision tables so we can restore them in HTML.

    tex4ht drops colortbl's shading, which the book uses in two ways:
      * the dmatrix / inlinedmatrix environments shade their header row and
        first column via \rowcolor / \columncolor — we tag each such table with
        a DMATRIXMARK token;
      * plain tables shade individual cells with \gr (\cellcolor) — we replace
        each \gr with a GRCELLMARK token left in the cell.
    shade_decision_tables() turns both markers into a `gr` class.
    """
    tex = re.sub(r'\\begin\{(dmatrix|inlinedmatrix)\}',
                 r'DMATRIXMARK\\begin{\1}', tex)
    tex = re.sub(r'\\gr\b', 'GRCELLMARK', tex)
    return tex


def escape_intext_links(tex):
    r"""Mark up references to examples and exercises so we can resolve them later.

    tex4ht resolves \ref to chapters and sections natively, but not \ref to the
    tcolorbox-counter labels used by examples (ex:...) and exercises (e:...). So
    we inject an ANCHOR marker carrying the label into each such box, and turn
    the matching \ref into a REF placeholder. restore_intext_links() then pairs
    them up using the number that tex4ht prints in the box title.
    """
    def inject(m):
        # The label may come from a `label=` key in the options or from a
        # \label{...} immediately following \begin{example}/\begin{exercise}.
        opts = m.groupdict().get('opts') or ''
        lm = re.search(r'label=([^,\]]+)', opts)
        label = lm.group(1).strip() if lm else (m.groupdict().get('lbl') or '').strip()
        if label:
            return m.group(0) + 'ANCHOR' + label + 'ENDANCHOR'
        return m.group(0)

    label_key = r'(?:\s*\\label\{(?P<lbl>[^}]+)\})?'
    # \begin{example}(Title)[label=ex:foo]   or   \begin{example}\label{ex:foo}
    tex = re.sub(r'\\begin\{example\}(?:\([^)]*\))?(?P<opts>\[[^\]]*\])?' + label_key,
                 inject, tex)
    # \begin{exercise}[Title]{daggers}[label=e:foo]   or   ...\label{e:foo}
    tex = re.sub(r'\\begin\{exercise\}(?:\[[^\]]*\])?\{[^}]*\}(?P<opts>\[[^\]]*\])?' + label_key,
                 inject, tex)
    # Turn \ref to example/exercise labels into placeholders.
    tex = re.sub(r'\\ref\{(ex?:[^}]+)\}', r'REF\1ENDREF', tex)
    return tex


def make4ht(verbose=False):
    """Run make4ht to create HTML."""
    tex4ht_options = [
        '2',          # split at chapter level
        'mathjax',    # use MathJax for math
        'tikz',       # convert TikZ diagrams to SVG
        'enumerate+', # enumerated list elements that keep the list counter value
        'fn-in',      # footnotes on each html page
    ]
    command = (
        f'cd {tmp_path} && '
        'make4ht '
        f'{"-a debug " if verbose else ""}'
        '-c mytex4ht.cfg '
        '--xetex '
        '--utf8 '
        '-f html5 '
        f'{main_tex} '
        f'"{",".join(tex4ht_options)}" '
        f'-d ../{html_path} '
        '&& cd -'
    )
    print(command)
    result = subprocess.run(command, shell=True, check=False, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print("Command failed with exit status", result.returncode)
        if result.stderr:
            print(result.stderr)


def save_or_restore_make4ht_output(restore=False):
    """Save make4ht output to allow fake runs (-f) for debugging the postprocessing."""
    if not restore:
        shutil.rmtree(tmp_path + '/html', ignore_errors=True)
        shutil.copytree(html_path, tmp_path + '/html')
    else:
        # keep the hand-maintained CSS!
        shutil.copyfile(html_path + '/' + css_file, tmp_path + '/html/' + css_file)
        shutil.rmtree(html_path)
        shutil.copytree(tmp_path + '/html', html_path)


def jobname():
    """Return the make4ht jobname (master file without extension)."""
    return os.path.splitext(main_tex)[0]


def rename_html_files():
    """Rename HTML files to match chapter filenames."""
    job = jobname()
    mapping = {}
    mapping[job + 'li1.html'] = 'toc.html'
    # Rename '<job>ch1.html' to '01-overview.html', etc.:
    tex_chapters = tex_files()
    for f in os.listdir(html_path):
        m = re.search(re.escape(job) + r'ch(\d+).*\.html', f)
        if m:
            chapter_num = m.group(1)
            if len(chapter_num) == 1:
                chapter_num = '0' + chapter_num
            try:
                chapter_file = next(ch for ch in tex_chapters if ch.startswith(chapter_num))
                new_name = chapter_file.replace('.tex', '.html')
                mapping[f] = new_name
            except StopIteration:
                print("No chapter file found for", f)
    for old, new in mapping.items():
        print("Renaming", old, "to", new)
        shutil.move(html_path + '/' + old, html_path + '/' + new)
    adjust_links(mapping)


def adjust_links(mapping):
    """Adjust links in HTML files."""
    for htmlfile in os.listdir(html_path):
        if not htmlfile.endswith('.html'):
            continue
        html = read_file(html_path + '/' + htmlfile)
        # Sort by key length descending to avoid partial replacements
        for old, new in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            html = html.replace(old, new)
        write_file(html_path + '/' + htmlfile, html)


def restore_intext_links():
    r"""Resolve the example/exercise references marked up by escape_intext_links.

    First pass: for every example/exercise box, read the number tex4ht printed
    in its title, pair it with the label carried by the injected ANCHOR marker,
    record label -> (htmlfile, number), and drop an <a id="label"> at the box.
    Second pass: replace each REF...ENDREF placeholder with a link to that box
    (or, inside math, a bare number).
    """
    anchors = {}  # 'ex:miners' -> ('05-utility.html', '5.1')

    for htmlfile in html_files():
        html = read_file(html_path + '/' + htmlfile)

        def extract_anchor(match):
            anchors[match.group(2)] = (htmlfile, match.group(1))
            head = match.group(0).split('ANCHOR')[0]
            return head + '<a id="' + match.group(2) + '"></a>'

        # 'Example 5.1 (Title)</p></div><div ...><p ...>ANCHORex:fooENDANCHOR'
        pattern = r"""
            (?:Example|Exercise)
            \s*([\d\.]+)              # the number tex4ht printed
            [^<]*?                    # optional title text, no tags
            (?:<\s*/?[^>]+>\s*)*      # the divs between title and content
            ANCHOR(.+?)ENDANCHOR
        """
        html = re.sub(pattern, extract_anchor, html, flags=re.DOTALL | re.VERBOSE)
        # drop any stray markers (e.g. from boxes whose title we couldn't parse):
        html = re.sub(r'ANCHOR(.+?)ENDANCHOR', '', html)
        write_file(html_path + '/' + htmlfile, html)

    for htmlfile in html_files():
        html = read_file(html_path + '/' + htmlfile)

        def replace_ref(match, link=True):
            label = match.group(1)
            if label not in anchors:
                print('Missing anchor:', label)
                return '??'
            filename, num = anchors[label]
            if not link:
                return num
            return f'<a class="locallink" href="{filename}#{label}">{num}</a>'

        html = sub_refs_html_aware(html, replace_ref)
        write_file(html_path + '/' + htmlfile, html)


def sub_refs_html_aware(html, replace_ref):
    """Replace REF placeholders, emitting bare numbers inside math blocks."""
    out = []
    last = 0
    for m in _HTML_MATH_REGION.finditer(html):
        out.append(re.sub(r'REF(.+?)ENDREF', replace_ref, html[last:m.start()]))
        out.append(re.sub(r'REF(.+?)ENDREF',
                          lambda r: replace_ref(r, link=False), m.group(0)))
        last = m.end()
    out.append(re.sub(r'REF(.+?)ENDREF', replace_ref, html[last:]))
    return ''.join(out)


def fix_html():
    """Fix HTML files after conversion."""
    restore_intext_links()
    for htmlfile in html_files():
        html = read_file(html_path + '/' + htmlfile)
        html = remove_comments(html)
        html = embed_in_template(html, htmlfile)
        html = fix_tcolorboxes(html, htmlfile)
        html = shade_decision_tables(html)
        html = fix_gtaper(html)
        html = fix_box_titles(html)
        html = fix_item_labels(html)
        html = fix_layout(html)
        validate_html(html, htmlfile)
        write_file(html_path + '/' + htmlfile, html)


def remove_comments(html):
    """Remove comments from HTML."""
    return re.sub(r'<!--.+?-->', '', html, flags=re.DOTALL)


def embed_in_template(html, filename):
    """Embed HTML files in template."""
    template = read_file('html_template.html')
    template = template.replace('{{year}}', str(datetime.datetime.now().year))
    toc = read_toc()
    template = template.replace('{{toc}}', '\n'.join(toc))
    body = re.split(r'<body\s*>', html, maxsplit=1)[1].rsplit('</body')[0]
    body = re.sub(r'<div class=.crosslinks.>.+?</div>', '', body, flags=re.DOTALL)
    # insert link to next chapter:
    chapter_toc = (t for t in toc if 'chapterToc' in t)
    try:
        next(t for t in chapter_toc if filename in t)
        next_link = next(chapter_toc)
        body += f'<div class="nextchapter">Next chapter: {next_link}</div>'
    except StopIteration:
        pass
    template = template.replace("{{content}}", body)
    title = 'Belief, Desire, and Rational Choice'
    m = re.search(r'<h2 class=.chapterHead[^>?]+>(.+)</h2>', body, flags=re.DOTALL)
    if m:
        title += ' | ' + re.sub(r'<[^>]+>', '', m.group(1))
    template = template.replace("{{title}}", title)
    return template


def read_toc():
    """Return TOC as list of <a>s."""
    toc_html = read_file(html_path + '/toc.html')
    # <span class="chapterToc">1 <a href="01-overview.html">Modelling Rational Agents</a></span>
    # <span class="sectionToc">1.1  <a href="01-overview.html#overview">Overview</a></span>
    toc_links = re.findall(r'<span class=.(chapterToc|sectionToc).>\s*([\d.]*)\s*<a href=.([^"\']+).>(.+?)</a>', toc_html)
    toc = [f'<a class="{level}" href="{href}">{num} {name}</a>' for level, num, href, name in toc_links]
    if len(toc) == 0:
        print("TOC not found in toc.html")
    return toc


def fix_item_labels(html):
    r"""Restore item labels that were escaped in LaTeX.

    <li> ITEMLABEL(*)ENDITEMLABEL => <li class="nobullet"><span class="itemlabel">(*)</span>
    """
    html = re.sub(r'<li[^>]*>\s*(?:<p[^>]*>)?\s*ITEMLABEL(.+?)ENDITEMLABEL',
                  r'<li class="nobullet"><span class="itemlabel">\1</span>',
                  html, flags=re.DOTALL)
    # remove ITEMLABEL...ENDITEMLABEL accidentally inserted into other kinds of items:
    html = re.sub(r'ITEMLABEL.+?ENDITEMLABEL', '', html)
    # remove orphaned </p> tags before </li>:
    html = re.sub(r'\s*</p>\s*(</li>)', r'\1', html)
    return html


def fix_layout(html):
    """Fix layout issues in HTML."""
    html = fix_mathjax_linebreaks(html)
    # remove anchors in lists that add a linebreak:
    html = re.sub(r'(<li class=.enumerate.[^>]*>)\s*<a\s+id=.[^\'"]+[\'"]></a>', r'\1', html)
    # strip trailing whitespace before </p> so justify does not stretch the last line:
    html = re.sub(r'\s+</p>', '</p>', html)
    # remove whitespace before section titles:
    html = re.sub(r'(<span class=.titlemark.>.+?</span>)(?:\s|\xa0|&nbsp;)*', r'\1', html)
    # remove empty table rows:
    html = re.sub(r'<tr>\s*<td[^>]*>\s*</td>\s*</tr>', '', html)
    return html


def fix_mathjax_linebreaks(html):
    r"""Avoid line breaks falling right after an inline math element.

    MathJax turns '... \( x \);' into '...</mjx-container>;' and nothing
    prevents a line break just before the semicolon. We wrap such cases in a
    no-wrap span.
    """
    html = re.sub(r'(\\\((?:[^\\)]|\\[^)])+\\\)[;.,?!\)])', r'<span class="nowrap">\1</span>', html)
    html = re.sub(r'(‘\\\((?:[^\\)]|\\[^)])+\\\)’?)', r'<span class="nowrap">\1</span>', html)
    return html


def validate_html(html, filename):
    """Validate HTML5 structure using html5lib and report issues."""
    parser = HTMLParser(namespaceHTMLElements=False)
    parser.parse(html)

    if parser.errors:
        print(f"WARNING: Validation issues in {filename}:")
        for (line, col), errorcode, datavars in parser.errors:
            message = constants.E.get(errorcode, errorcode)
            if isinstance(message, str) and datavars:
                try:
                    message = message % datavars
                except (TypeError, KeyError):
                    pass
            print(f"  Line {line}, Col {col}: {message}")


def fix_tcolorboxes(html, htmlfile):
    """Tidy up tcolorbox divs.

    tex4ht sometimes gives a box the duplicate class "tcolorbox tcolorbox",
    which makes it impossible to style specifically. We rely on BeautifulSoup to
    balance any tags that tex4ht left unclosed.
    """
    soup = BeautifulSoup(html, 'html.parser')  # auto-closes elements
    for tbox in soup.find_all('div', class_='tcolorbox'):
        classes = tbox.get('class', [])
        if classes.count('tcolorbox') > 1:
            tbox['class'] = ['tcolorbox', 'obs']
    return str(soup)


def shade_decision_tables(html):
    r"""Restore the gray header-row / first-column shading of decision tables.

    The dmatrix / inlinedmatrix environments shade their first row and first
    column via colortbl, which tex4ht drops. Each such table was marked with a
    DMATRIXMARK token (see mark_decision_tables); here we tag the table with a
    `dmatrix` class and add a `gr` class to its header-row and first-column
    cells, which the stylesheet shades.
    """
    # Attach the marker to the table that immediately follows it (without
    # leaping across another marker), adding a `dmatrix` class.
    html = re.sub(r'DMATRIXMARK((?:(?!DMATRIXMARK).)*?)<table class="tabular"',
                  r'\1<table class="tabular dmatrix"', html, flags=re.DOTALL)
    # drop the now-empty paragraph the marker may have left behind:
    html = re.sub(r'<p[^>]*>\s*</p>\s*(<div class="tabular">\s*'
                  r'<table class="tabular dmatrix")', r'\1', html)
    html = html.replace('DMATRIXMARK', '')  # tidy up any orphaned markers

    if 'tabular dmatrix' not in html and 'GRCELLMARK' not in html:
        return html

    def add_gr(cell):
        if 'gr' not in (cell.get('class') or []):
            cell['class'] = (cell.get('class') or []) + ['gr']

    soup = BeautifulSoup(html, 'html.parser')
    # dmatrix / inlinedmatrix: shade header row and first column structurally.
    for table in soup.select('table.dmatrix'):
        content_rows = [r for r in table.find_all('tr')
                        if 'hline' not in (r.get('class') or [])]
        for i, row in enumerate(content_rows):
            for j, td in enumerate(row.find_all('td')):
                if i == 0 or j == 0:           # header row or first column
                    add_gr(td)
    # plain tables: shade the individual cells marked with \gr.
    for cell in soup.find_all(['td', 'th']):
        if 'GRCELLMARK' in cell.get_text():
            add_gr(cell)
    return str(soup).replace('GRCELLMARK', '')


def fix_gtaper(html):
    r"""Render the \scaleto-based 'uniform hypothesis' G-rows as plain HTML.

    Chapter 4 depicts the uniform/non-uniform hypotheses as 101 'G's that taper
    to a tiny smear in the middle, built with scalerel's \scaleto{Gs}{Npt}.
    MathJax can't scale individual glyphs reliably, so we pull these decorative
    \(...\scaleto...\) blocks out of math and emit sized <span>s instead.
    """
    token_re = re.compile(
        r'\\scaleto\s*\{([^{}]*)\}\{([^{}]*)\}'   # \scaleto{Gs}{Npt}
        r'|\{\\scriptstyle\s+([A-Za-z]+)\}'       # {\scriptstyle G}
        r'|\{\\scriptscriptstyle\s+([A-Za-z]+)\}' # {\scriptscriptstyle G}
        r'|([A-Za-z]+)'                           # full-size letters (G's, final R)
    )

    # Map scalerel's target point sizes to pixels. A sub-pixel font-size (the
    # 0.1pt middle) renders as a solid line, so clamp to a visible floor; the
    # source already means the middle to be a uniform tiny block.
    scale_px, floor_px = 2.5, 4.5

    def size_px(pt_str):
        pt = float(re.sub(r'pt$', '', pt_str.strip()))
        return f'{max(pt * scale_px, floor_px):.1f}px'

    def repl(m):
        block = m.group(0)
        if r'\scaleto' not in block:
            return block
        out = ['<span class="gtaper">']
        for t in token_re.finditer(m.group(1)):
            if t.group(1) is not None:                       # \scaleto
                gs = re.sub(r'\s+', '', t.group(1))
                out.append(f'<span style="font-size:{size_px(t.group(2))}">{gs}</span>')
            elif t.group(3):                                 # \scriptstyle
                out.append(f'<span style="font-size:0.7em">{t.group(3)}</span>')
            elif t.group(4):                                 # \scriptscriptstyle
                out.append(f'<span style="font-size:0.5em">{t.group(4)}</span>')
            elif t.group(5):                                 # full size
                out.append(t.group(5))
        out.append('</span>')
        return ''.join(out)

    return re.sub(r'\\\((.*?)\\\)', repl, html, flags=re.DOTALL)


def fix_box_titles(html):
    """Promote a leading bold run inside a titleless box into its title.

    Some boxes (e.g. exercises whose heading is typeset via `before upper`)
    put their heading in the content rather than in a separate title div.
    """
    html = re.sub(
        r'(class="tcolorbox exercise"[^>]*>)\s*<div class="tcolorbox-title">\s*</div>'
        r'(\s*<div class="tcolorbox-content">.*?)<strong>([^<]+)</strong>\s*',
        r'\1<div class="tcolorbox-title">\3</div>\2',
        html,
        flags=re.DOTALL
    )
    return html


def create_index():
    """Create index.html from the table of contents."""
    html = read_file(html_path + '/toc.html')
    html = re.sub(r'<h2.+?</h2>', '', html)
    shutil.copyfile('doclicense.png', html_path + '/doclicense.png')
    write_file(html_path + '/index.html', html)


def check_links():
    """Check for missing link targets ('??')."""
    for htmlfile in html_files():
        html = read_file(html_path + '/' + htmlfile)
        if '??' in html:
            print("Missing link targets in", htmlfile)


def read_file(filename):
    """Read file and return contents."""
    with open(filename) as f:
        return f.read()


def write_file(filename, data):
    """Write data to file."""
    with open(filename, mode="wt") as f:
        f.write(data)


if __name__ == "__main__":
    main()

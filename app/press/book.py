import os
import re
import subprocess

import jinja2
from jinja2 import Environment


def save(book, path):
    with open(path, "w") as f:
        f.write(book)


def compile_verses(src):
    # add \verse before every verse
    result = re.sub(r"(?:\n\n|^)", "\n\n\\\\verse\n", src, count=0, flags=0)

    # add \\ to every non-empty line
    result = re.sub(r"([^\n]+)", r"\1 \\\\", result)

    result = "\\begin{song}" + result + "\\end{song}"
    return result


def compile_lytex(src):
    return "\\begin{lilypond}\n" + src + "\n\\end{lilypond}"


def bake(songs, templates_dir):
    for song in songs:
        song.verses = compile_verses(song.verses)
        song.lytex = compile_lytex(song.lytex)

    env = Environment(
        block_start_string="{+",
        block_end_string="+}",
        loader=jinja2.FileSystemLoader(templates_dir),
    )
    book_template = env.get_template("book.jinja2")
    book = book_template.render({"songs": songs})

    lytex_path = "test" + ".lytex"
    save(book, lytex_path)

    proc = subprocess.Popen(
        ["lilypond-book", "--output=" + "output", "--pdf", lytex_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.communicate()
    #    subprocess.run(['lilypond-book', '--output=' + "output", '--pdf', lytex_path])
    orig_dir = os.path.abspath(".")
    os.chdir("output")
    proc = subprocess.Popen(
        ["pdflatex", "-interaction=nonstopmode", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        proc.communicate()
    except Exception as e:
        print(e)
        os.chdir(orig_dir)
    os.chdir(orig_dir)

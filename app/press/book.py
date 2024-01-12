import re
import subprocess
from pathlib import Path

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


def bake(songs, songbook, templates_dir):
    for song in songs:
        song.verses = compile_verses(song.verses)
        song.lytex = compile_lytex(song.lytex)

    env = Environment(
        block_start_string="{+",
        block_end_string="+}",
        loader=jinja2.FileSystemLoader(templates_dir),
    )
    book_template = env.get_template("book.jinja2")
    book = book_template.render({"songs": songs, "songbook": songbook})

    dest_path = Path("app/tmp/songbooks/" + str(songbook.songbook_id))
    dest_path.mkdir(parents=True, exist_ok=True)
    lytex_path = dest_path / ("songbook" + ".lytex")
    output_path = dest_path / "output"
    tex_path = output_path / ("songbook" + ".tex")
    save(book, lytex_path)

    proc = subprocess.Popen(
        ["lilypond-book", "--output=" + str(output_path), "--pdf", lytex_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.communicate()
    #    subprocess.run(['lilypond-book', '--output=' + "output", '--pdf', lytex_path])
    #    orig_dir = os.path.abspath(".")
    #    os.chdir("output")
    proc = subprocess.Popen(
        [
            "pdflatex",
            "--interaction=nonstopmode",
            "--output-directory=" + str(output_path),
            str(tex_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        proc.communicate()
    except Exception as e:
        print(e)

    return output_path / "songbook.pdf"


#        os.chdir(orig_dir)
#    os.chdir(orig_dir)

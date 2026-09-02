import os
import subprocess
import sys


def compile_latex_paper():
    paper_dir = os.path.dirname(os.path.abspath(__file__))
    main_tex = os.path.join(paper_dir, "main.tex")

    if not os.path.exists(main_tex):
        print(f"Error: Could not find {main_tex}")
        sys.exit(1)

    print("Building LaTeX Paper: main.tex -> main.pdf...")

    # Step 1: pdflatex (Pass 1)
    print("Pass 1: Running pdflatex...")
    cmd1 = ["pdflatex", "-interaction=nonstopmode", "main.tex"]
    subprocess.run(cmd1, cwd=paper_dir, capture_output=True)

    # Step 2: bibtex (Process citations)
    print("Pass 2: Running bibtex...")
    cmd2 = ["bibtex", "main"]
    subprocess.run(cmd2, cwd=paper_dir, capture_output=True)

    # Step 3: pdflatex (Pass 2)
    print("Pass 3: Running pdflatex...")
    subprocess.run(cmd1, cwd=paper_dir, capture_output=True)

    # Step 4: pdflatex (Pass 3 - resolve references)
    print("Pass 4: Finalizing references with pdflatex...")
    res = subprocess.run(cmd1, cwd=paper_dir, capture_output=True)

    output_pdf = os.path.join(paper_dir, "main.pdf")
    if os.path.exists(output_pdf):
        print(f"Success! Generated {output_pdf}")
    else:
        print("Build complete (check log for details).")


if __name__ == "__main__":
    compile_latex_paper()

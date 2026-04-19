import glob
import os
import sass


def build_core_html(base_dir: str = 'frontend'):
    """Rebuild frontend/core.html from head.html + all page*.html + head2.html."""
    head_path = os.path.join(base_dir, 'head.html')
    tail_path = os.path.join(base_dir, 'head2.html')

    try:
        with open(head_path, 'r', encoding='utf-8') as f:
            head_html = f.read()
        with open(tail_path, 'r', encoding='utf-8') as f:
            tail_html = f.read()

        page_parts = []
        for page_file in sorted(glob.glob(os.path.join(base_dir, 'page*.html'))):
            with open(page_file, 'r', encoding='utf-8') as f:
                page_parts.append(f.read())

        combined = head_html + "\n" + "\n".join(page_parts) + "\n" + tail_html

        core_path = os.path.join(base_dir, 'core.html')
        with open(core_path, 'w', encoding='utf-8') as f:
            f.write(combined)
        print(f"Rebuilt {core_path} from head.html, page*.html, and head2.html")
    except Exception as e:
        print(f"Failed to build core.html: {e}")


def compile_scss(refresh_cb=None, pattern: str = 'frontend/**/*.scss'):
    scss_files = glob.glob(pattern, recursive=True)
    for scss_file in scss_files:
        css_file = scss_file[:-5] + '.css'
        try:
            css = sass.compile(filename=scss_file, output_style='expanded')
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(css)
            print(f"Compiled {scss_file} to {css_file}")
            if refresh_cb:
                refresh_cb()
        except Exception as e:
            print(f"Failed to compile {scss_file}: {e}")


def html_update(refresh_cb=None):
    print("HTML file changed, reloading...")
    if refresh_cb:
        refresh_cb()

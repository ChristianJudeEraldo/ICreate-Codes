import os
import time
import threading


def read_set_page_file(set_page_path: str):
    try:
        with open(set_page_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"{set_page_path} not found")
        return None
    except Exception as e:
        print(f"Failed to read {set_page_path}: {e}")
        return None

    page = (raw or '').strip().splitlines()[0].strip() if raw is not None else ''
    page = page.lstrip('#').strip()
    page = page.lstrip('/\\').strip()
    return page or None


def start_set_page_listener(eel, set_page_path: str, poll_interval_s: float = 0.25):
    def _worker():
        last_mtime = None
        while True:
            try:
                mtime = os.path.getmtime(set_page_path)
                if last_mtime is None:
                    last_mtime = mtime
                elif mtime != last_mtime:
                    last_mtime = mtime
                    page = read_set_page_file(set_page_path)
                    if page:
                        print(f"set_page.txt changed, navigating to: {page}")
                        eel.goToPage(page)
                    else:
                        print("set_page.txt changed, but no page was specified")
            except FileNotFoundError:
                last_mtime = None
            except Exception as e:
                print(f"set_page.txt monitor error: {e}")
            time.sleep(poll_interval_s)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t

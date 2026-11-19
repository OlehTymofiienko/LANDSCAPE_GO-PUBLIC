#!/usr/bin/env python3
"""LANDSCAPE_GO unified launcher. Use --cli for console, default to Tk on desktop."""
import os, sys
from GAME.cli import parse_args,run

def configure_windows_output():
    """Keep redirected Windows CLI output Unicode-safe; honor explicit encoding."""
    if sys.platform == 'win32' and not os.environ.get('PYTHONIOENCODING'):
        for stream in (sys.stdout, sys.stderr):
            if stream is not None and hasattr(stream, 'reconfigure') and not stream.isatty():
                stream.reconfigure(encoding='utf-8', errors='backslashreplace')

def main():
    configure_windows_output()
    args=parse_args()
    if args.cli or args.verify or args.catalog or args.list or args.maps or args.source or '--size' in sys.argv or '--lesson' in sys.argv or '--mode' in sys.argv:
        return run(args)
    try:
        from GAME.gui import main as gui_main
        return gui_main()
    except (ImportError,RuntimeError) as ex:
        print('Графический режим недоступен, переключаюсь в консоль:',ex)
        return run(args)

if __name__=='__main__':sys.exit(main())

import cmd
import sys
import os

from tri_photo_date import sort_photos
from tri_photo_date.sort_photos import CFG

from tri_photo_date.config.config_paths import IMAGE_DATABASE_PATH
from tri_photo_date.utils.constants import FILE_SIMULATE, FILE_MOVE, FILE_COPY

FILE_MODES = dict(zip((FILE_SIMULATE, FILE_COPY, FILE_MOVE), ('simulation, no files will be affected', 'copying files', 'moving files')))

TRUE = ['1', 'y','yes', 'true', True]
FALSE = ['0', 'n', 'no', 'false', False]

if os.name == 'nt':
    W  = ''
    R  = ''
    G  = ''
    O  = ''
    B  = ''
    P  = ''
    BB = ''
    BG = ''
    BW = ''
else:
    W  = '\033[0m'  # white (normal)
    R  = '\033[31m' # red
    G  = '\033[32m' # green
    O  = '\033[33m' # orange
    B  = '\033[34m' # blue
    P  = '\033[35m' # purple
    BB = '\033[94m' # bright blue
    BG = '\033[92m' # bright green
    BW = '\033[97m' # bright white

from itertools import islice

def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch

DEFAULT_CONFIG_TOML = "/home/david/Prog/tri_photo_date/tri_photo_date/config/default_config.toml"
from tomlkit import parse

def flatten_dct(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key.lower() + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dct(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

import re
reg_split = re.compile('\s*=.*#\s*')


def get_config_comments():

    with open(DEFAULT_CONFIG_TOML, 'r') as f:
        doc = parse(f.read())

    dct = {}
    for key, value in doc.items():
        for com, *kNt in batched(value.as_string().split('\n'), 2):
            if kNt:
                k, *t = reg_split.split(kNt[0])
                dct[key.lower() + '.' + k] = {}
                dct[key.lower() + '.' + k]['comment'] = com.strip('# ')
                dct[key.lower() + '.' + k]['type'] = '' if not t else t[0]
    #for k,v in dct.items():
    #    print('---', k , '---')
    #    for k2, v2 in v.items():
    #        print(k2, ':', v2)
    return dct

CONFIG_COMMENTS = get_config_comments()


table_color = lambda xs : (c + x + W for c, x in zip([R,G,B], xs))
def type_color(t):
    if t == "int":
        return B
    elif t == 'float':
        return B
    elif t == 'string' or t == "list of strings":
        return O
    elif t == 'bool':
        return G
    else:
        return W

def pprint(dct, section=""):
    for k,v in dct.items():
        k = '.'.join((section,k)) if section else k
        print('.'.join(x+y for x,y in zip((B,BB),k.rsplit('.',1))), ':', W)
        print('description :', CONFIG_COMMENTS[k]['comment'])
        print('type :', O+ CONFIG_COMMENTS[k]['type']+W)
        print('value :', type_color(CONFIG_COMMENTS[k]['type'])+str(v).strip('()').replace("'",'').strip(',')+W)
        print()

class TriphotoShell(cmd.Cmd):
    intro = 'Welcome to the Triphoto shell. Type help or ? to list commands.\n'
    prompt = '(triphoto) '
    dct = CFG

    def do_get(self, arg):
        "Get a parameter value"

        if arg:
            section, *param = arg.split()
            if param:
                param = param[0]
                pprint({param:self.dct[section][param]}, section)
            else:
                pprint(self.dct[section], section)
        else:
            pprint(flatten_dct(self.dct))

    def do_set(self, arg):
        "Set a paramter to given value"

        section, param, *value = arg.split()
        value = ' '.join(value)
        self.dct[(section.lower(),param)] = value

    def do_scan(self, arg):
        "Scan source and dest folder for files"

        print(f"Scan of source and destination folder will be performed with those parameters :\nscan.src_dir = {CFG['scan.src_dir']}\nscan.dest_dir = {CFG['scan.dest_dir']=}\n")
        #is_ok = input('Continue? [Y/n]')
        is_ok = True
        if not is_ok or is_ok in TRUE:
            sort_photos.populate_db()

    def do_process(self, arg):
        "Generate new paths for images files"

        sort_photos.compute()

    def do_execute(self, arg):
        "Copy/Move files given path generated at process step, run 'triphoto preview' to check paths"

        print(f"\nAction mode = {CFG['action.action_mode']}, start {FILE_MODES[CFG['action.action_mode']]}\n")
        sort_photos.execute()

    def do_preview(self, arg):
        "Show generated paths for each files"

        import sqlite3

        # create a connection to the database file (or create it if it doesn't exist)
        conn = sqlite3.connect(IMAGE_DATABASE_PATH)

        # create a cursor object to interact with the database
        cursor = conn.cursor()

        # select data from the table
        cursor.execute('SELECT filename, new_folder, new_filename FROM process_preview;')
        results = cursor.fetchall()

        header = ('old_name', 'new_folder', 'new_filename')
        print(
            '\npreview of new folder and names,'
            'press enter to continue, type q to quit',
            '\t'.join(table_color(header)),
            '-' * len('\t'.join(header)+'\ŧ'*7), sep="\n"
        )

        for row in results:
            print('\t'.join(table_color(row)), end='\n', flush=True)
            if input().strip('\n') == 'q' :
                break

        conn.close()

        print('\n')

        pass

    def complete_get(self, text, line, begidx, endidx):

        line_elt=line.split()
        if len(line_elt) == 1 or (len(line_elt) == 2 and text):
            sections = [s for s in self.dct.keys()]
        else: #len(line_elt) == 2 and not text:
            sections = [k for k in self.dct[line_elt[1]].keys()]
        if not text:
            return sections
        else:
            return [s + ' ' for s in sections if s.startswith(text)]

    def complete_set(self, text, line, begidx, endidx):

        line_elt=line.split()
        if len(line_elt) == 1 or (len(line_elt) == 2 and text):
            sections = [s for s in self.dct.keys()]
        else: #len(line_elt) == 2 and not text:
            sections = [k for k in self.dct[line_elt[1]].keys()]
        if not text:
            return sections
        else:
            return [s + ' ' for s in sections if s.startswith(text)]

    def do_q(self, arg):
        "exit"
        return True

    def do_exit(self, arg):
        "exit"
        return True

def cli_run():
    #sort_photos.populate_db()
    #sort_photos.compute()
    #sort_photos.execute()
   # ask_config()
    shell = TriphotoShell()

    if len(sys.argv) > 2:
        shell.onecmd(' '.join(sys.argv[2:]))
    else:
        shell.cmdloop()


def ask_config():

    for section in CFG.config.sections():
        items = CFG.config.items(section)
        for param, value in items:
            print(f'   {param} = {value}')
        is_change = input('Change parameters [y/N] ?')

        if is_change.lower() in TRUE:
            for param, value in items:
                CFG[(section, param)] = input(f'{param} = ')

    print(CFG)

    #CFG = {}
    #CFG["scan.src_dir"]
    #CFG["scan.dest_dir"]
    #CFG["scan.is_use_cached_datas"]

    #CFG["source.dir"]
    #CFG["source.extentions"]
    #CFG["source.cameras"]
    #CFG["source.is_recursive"]
    #CFG["source.excluded_dirs"]
    #CFG["source.exclude_toggle"]
    #CFG["source.is_exclude_dir_regex"]

    #CFG["destination.dir"]
    #CFG["destination.rel_dir"]
    #CFG["destination.filename"]

    #CFG["duplicates.is_control"]
    #CFG["duplicates.mode"]
    #CFG["duplicates.is_scan_dest"]

    #CFG["options.name.guess_fmt"]
    #CFG["options.name.is_guess"]
    #CFG["options.group.is_group"]
    #CFG["options.group.display_fmt"]
    #CFG["options.group.floating_nb"]
    #CFG["options.gps.is_gps"]
    #CFG["options.general.is_delete_metadatas"]
    #CFG["options.general.is_date_from_filesystem"]
    #CFG["options.general.is_force_date_from_filesystem"]

    #CFG["action.action_mode"]

    #CFG["interface.mode"]
    #CFG["interface.lang"]
    #CFG["interface.size"]

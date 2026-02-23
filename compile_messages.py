"""
Simple .po to .mo compiler for Django with proper UTF-8 encoding
"""
import struct
import os

def make_mo(po_path, mo_path):
    messages = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('msgid "'):
            if current_msgid is not None:
                messages[current_msgid] = current_msgstr or ''
            current_msgid = line[7:-1]
            current_msgstr = None
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr "'):
            current_msgstr = line[8:-1]
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and line.endswith('"'):
            continuation = line[1:-1]
            if in_msgstr and current_msgstr is not None:
                current_msgstr += continuation
            elif in_msgid and current_msgid is not None:
                current_msgid += continuation
        
        i += 1
    # Add last entry
    if current_msgid is not None:
        messages[current_msgid] = current_msgstr or ''
    
    # The empty msgid entry must contain charset info
    header = (
        b'Project-Id-Version: MitsuList 1.0\n'
        b'Report-Msgid-Bugs-To: \n'
        b'POT-Creation-Date: 2026-02-06 00:00+0000\n'
        b'PO-Revision-Date: 2026-02-06 00:00+0000\n'
        b'Last-Translator: MitsuList Team\n'
        b'Language-Team: Ukrainian\n'
        b'Language: uk\n'
        b'MIME-Version: 1.0\n'
        b'Content-Type: text/plain; charset=UTF-8\n'
        b'Content-Transfer-Encoding: 8bit\n'
        b'Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);\n'
    ).decode('utf-8')
    messages[''] = header
    
    # Sort by msgid (but empty string must be first)
    keys = sorted([k for k in messages.keys() if k != ''])
    keys = [''] + keys
    
    # Generate .mo file structure
    offsets = []
    ids = b''
    strs = b''
    
    for key in keys:
        key_bytes = key.encode('utf-8')
        val_bytes = messages[key].encode('utf-8')
        offsets.append((len(ids), len(key_bytes), len(strs), len(val_bytes)))
        ids += key_bytes + b'\x00'
        strs += val_bytes + b'\x00'
    
    # Header values
    MAGIC = 0x950412de
    VERSION = 0
    nstrings = len(keys)
    keystart = 7 * 4
    valuestart = keystart + nstrings * 8
    
    output = []
    output.append(struct.pack('Iiiiiii', MAGIC, VERSION, nstrings, keystart, valuestart, 0, 0))
    
    ids_offset = valuestart + nstrings * 8
    strs_offset = ids_offset + len(ids)
    
    for o in offsets:
        output.append(struct.pack('ii', o[1], ids_offset + o[0]))
    for o in offsets:
        output.append(struct.pack('ii', o[3], strs_offset + o[2]))
    
    output.append(ids)
    output.append(strs)
    
    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, 'wb') as f:
        for data in output:
            f.write(data)
    
    print(f'Created {mo_path} with {nstrings} translations (including header)')

if __name__ == '__main__':
    make_mo('locale/uk/LC_MESSAGES/django.po', 'locale/uk/LC_MESSAGES/django.mo')

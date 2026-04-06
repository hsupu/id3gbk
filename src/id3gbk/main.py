
# import chardet
# from chardet import (
#     mbcsgroupprober,
# )

from __future__ import annotations
import typing as t

import argparse
import copy
import glob
import os
import traceback

from shutil import copyfile

if t.TYPE_CHECKING:
    from mutagen import id3 as _id3
    from mutagen import apev2 as _apev2


enc_list: list[str] = [
    'gbk',
    # 'big5',
    'utf-8',
    'utf-32-le', 'utf-32-be', 'utf-32',
    'utf-16-le', 'utf-16-be', 'utf-16',
]

AUDIO_EXTS: set[str] = {
    '.mp3', '.mp2', '.mp1', '.mpa',
    '.m4a', '.mp4',
    '.ogg', '.opus',
    '.flac',
    '.wav', '.wv',
    '.ape',
    '.aac',
    '.wma',
    '.tta', '.tak',
    '.aiff', '.aif',
}


def dump(path: str, settings: argparse.Namespace) -> None:
    from mutagen import id3, apev2

    audioID3 = id3.ID3()
    try:
        audioID3.load(path)
    except id3.error as exc:
        print(exc)
        audioID3 = None

    if audioID3:
        print('ID3', repr(audioID3.version))
        for name, tag in audioID3.items():
            if not isinstance(tag, id3._frames.TextFrame):
                print(name, type(tag))
                continue
            print(name, repr(tag))
    else:
        print('No ID3')

    audioAPE = apev2.APEv2File()
    try:
        audioAPE.load(path)
    except apev2.error as exc:
        print(exc)
        audioAPE = None

    if audioAPE:
        print('APEv2 found')
        for k, v in audioAPE.items():
            if not isinstance(v, apev2.APETextValue):
                print(k, type(v))
                continue
            print(k, repr(v))
    else:
        print('No APEv2')


def process(path: str, settings: argparse.Namespace) -> None:
    from mutagen import id3, apev2

    verbose: int = getattr(settings, 'verbose', 0)
    dryrun: bool = getattr(settings, 'dryrun', False)
    print_repr: bool = getattr(settings, 'print_repr', False)
    include_ape: bool = getattr(settings, 'include_ape', False)
    force_utf16: bool = getattr(settings, 'force_utf16', False)

    if verbose > 2:
        print(settings)

    audioID3 = id3.ID3()
    try:
        audioID3.load(path)
    except id3._util.error as exc:
        print(exc)
        audioID3 = None

    audioAPE = apev2.APEv2File()
    if include_ape:
        try:
            audioAPE.load(path)
        except apev2.error as exc:
            print(exc)
            audioAPE = None

    if True \
            and (not audioID3 or len(audioID3) == 0) \
            and (not audioAPE or len(audioAPE) == 0):
        print('NoTags', path)
        return

    modified = False
    if audioID3:
        for name, tag in audioID3.items():
            if not isinstance(tag, id3._frames.TextFrame):
                if verbose > 0:
                    print('SKIP', name, type(tag))
                continue

            encoding = tag.encoding
            if encoding != id3._specs.Encoding.LATIN1:
                if not force_utf16:
                    if verbose > 0:
                        print('SKIP', name, encoding)
                    continue

            if verbose > 2:
                print(name, repr(tag))

            fixed = False
            # fix = tag.__class__()
            fix = copy.copy(tag) # 浅拷贝，保留其他字段（如有）
            fix.encoding = id3._specs.Encoding.UTF8
            fix.text = []

            for item in tag.text:
                # 部分标签的文本有包装类，如 ID3TimeStamp
                # if type(item) != str:
                #     print('WARN', name, type(item))
                orig = str(item)

                # 这里幸亏 latin1 是良好的中间编码，只用 latin1 反复解码再编码不会丢数据
                raw_bytes = orig.encode('latin1')

                # detector = chardet.UniversalDetector(
                #     lang_filter=chardet.enums.LanguageFilter.CJK,
                #     should_rename_legacy=True)
                # detector._charset_probers = [
                #     mbcsgroupprober.MBCSGroupProber(),
                # ]
                # detector.feed(bytes)
                # detect_result = detector.close()
                # print(name, detect_result)

                success = False
                text = orig  # fallback when no encoding succeeds
                for enc in enc_list:
                    try:
                        decoded = raw_bytes.decode(enc)
                        encoded = decoded.encode(enc)
                        if encoded == raw_bytes:
                            success = True
                            text = decoded
                            break
                        if verbose > 1:
                            print('MIS-ENCODING', enc)
                    except UnicodeDecodeError as exc:
                        if verbose > 1:
                            print(exc)
                        pass

                if not success:
                    print('BAD', repr(orig))

                if orig == text or not success:
                    fix.text.append(orig)
                    continue

                if verbose > 2:
                    print('CONV', enc, repr(orig), repr(text))
                fix.text.append(text)
                fixed = True

            if fixed:
                if verbose > 1:
                    print(name, 'SET', repr(fix))

                audioID3.add(fix)
                modified = True

    if audioAPE:
        for k, v in audioAPE.items():
            if not isinstance(v, apev2.APETextValue):
                continue

            if verbose > 2:
                print(k, repr(v))

            fixed = False

            orig = str(v)
            raw_bytes = orig.encode('utf-8')

            success = False
            text = orig
            for enc in enc_list:
                try:
                    decoded = raw_bytes.decode(enc)
                    encoded = decoded.encode(enc)
                    if encoded == raw_bytes:
                        success = True
                        text = decoded
                        break
                    if verbose > 1:
                        print('MIS-ENCODING', enc)
                except UnicodeDecodeError as exc:
                    if verbose > 1:
                        print(exc)
                    pass

            if not success:
                print('BAD', repr(orig))

            if orig == text or not success:
                continue

            if verbose > 1:
                print(k, 'SET', repr(text))

            audioAPE[k] = text
            modified = True

        modified = False

    if not modified:
        print('Unchanged', path)
        return

    if print_repr:
        print(repr(audioID3))
    else:
        try:
            print(audioID3.pprint())
        except Exception as exc:
            traceback.print_exception(exc)
            print(repr(audioID3))
            return

    print("FIX", path)
    if not dryrun:
        backup_path = os.path.dirname(path) + '/orig.' + os.path.basename(path)
        copyfile(path, backup_path)
        audioID3.save()


def expand_paths(patterns: list[str], *, exts: set[str] | None = None) -> list[str]:
    files: list[str] = []
    for pattern in patterns:
        expanded = glob.glob(pattern) or [pattern]
        for entry in expanded:
            if os.path.isdir(entry):
                for dirpath, _dirnames, filenames in os.walk(entry):
                    for fname in filenames:
                        if exts is not None and os.path.splitext(fname)[1].lower() not in exts:
                            continue
                        files.append(os.path.join(dirpath, fname))
            else:
                if exts is not None and os.path.splitext(entry)[1].lower() not in exts:
                    continue
                files.append(entry)
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str, nargs='+',
                        help='File path(s), glob pattern(s), or director(ies) to process')
    parser.add_argument('--include-ape', action='store_true')
    parser.add_argument('--force-utf16', action='store_true')
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('--print-repr', action='store_true')
    parser.add_argument('--ext', type=str, action='append', dest='exts', default=None,
                        help='Additional extension to include (e.g. .mp3); can be repeated')
    parser.add_argument('--verbose', type=int, default=0)
    args = parser.parse_args()
    # print(args)

    exts: set[str] | None = set(AUDIO_EXTS)
    if args.exts:
        exts.update(e.lower() for e in args.exts)

    items = expand_paths(args.path, exts=exts)
    print(f'Found {len(items)} : {", ".join(args.path)}')

    for path in items:
        if not os.path.exists(path):
            raise FileNotFoundError(f'FileNotExist: {path}')

        if args.dump:
            dump(path, args)
        else:
            process(path, args)

if __name__ == '__main__':
    main()

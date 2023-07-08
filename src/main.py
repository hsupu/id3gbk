
# import chardet
# from chardet import (
#     mbcsgroupprober,
# )

import copy
import os
import traceback

from shutil import copyfile


enc_list = [
    'gbk',
    # 'big5',
    'utf-8',
    'utf-32-le', 'utf-32-be', 'utf-32',
    'utf-16-le', 'utf-16-be', 'utf-16',
]


def dump(path, settings):
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


def process(path, settings):
    from mutagen import id3, apev2

    verbose = getattr(settings, 'verbose', 0)
    dryrun = getattr(settings, 'dryrun', False)
    print_repr = getattr(settings, 'print_repr', False)
    include_ape = getattr(settings, 'include_ape', False)
    force_utf16 = getattr(settings, 'force_utf16', False)

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
                bytes = orig.encode('latin1')

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
                for enc in enc_list:
                    try:
                        text = bytes.decode(enc)
                        encoded = text.encode(enc)
                        if encoded == bytes:
                            success = True
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
            bytes = orig.encode('utf-8')

            success = False
            for enc in enc_list:
                try:
                    text = bytes.decode(enc)
                    encoded = text.encode(enc)
                    if encoded == bytes:
                        success = True
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


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('--include-ape', action='store_true')
    parser.add_argument('--force-utf16', action='store_true')
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('--print-repr', action='store_true')
    parser.add_argument('--verbose', type=int, default=0)
    args = parser.parse_args()
    # print(args)

    path = args.path

    import os
    if not os.path.exists(path):
        print('FileNotExist', path)
        exit(0)

    if args.dump:
        dump(path, args)
    else:
        process(path, args)

if __name__ == '__main__':
    main()

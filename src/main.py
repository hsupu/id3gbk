
# import chardet
# from chardet import (
#     mbcsgroupprober,
# )

import copy
import os
import traceback

from shutil import copyfile


def process(path, settings):
    from mutagen import id3

    readonly = getattr(settings, 'readonly', False)
    verbose = getattr(settings, 'verbose', 0)
    print_repr = getattr(settings, 'print_repr', False)

    try:
        audio = id3.ID3(path)
    except id3._util.ID3NoHeaderError as exc:
        print(exc)
        return

    modified = False
    for name, tag in audio.items():
        if not isinstance(tag, id3._frames.TextFrame):
            if verbose > 0:
                print('SKIP', name, type(tag))
            continue

        encoding = tag.encoding
        if encoding != id3._specs.Encoding.LATIN1:
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

            enc_list = [
                'gbk',
                # 'big5',
                'utf-8',
                'utf-32-le', 'utf-32-be', 'utf-32',
                'utf-16-le', 'utf-16-be', 'utf-16',
            ]

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

            audio.add(fix)
            modified = True

    if not modified:
        print('Unchanged', path)
        return

    if print_repr:
        print(repr(audio))
    else:
        try:
            print(audio.pprint())
        except Exception as exc:
            traceback.print_exception(exc)
            print(repr(audio))
            return

    print("FIX", path)
    if not readonly:
        backup_path = os.path.dirname(path) + '/orig.' + os.path.basename(path)
        copyfile(path, backup_path)
        audio.save()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('--readonly', action='store_true')
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--print-repr', action='store_true')
    args = parser.parse_args()
    # print(args)

    path = args.path

    import os
    if not os.path.exists(path):
        print('FileNotExist', path)
        exit(0)

    process(path, args)

if __name__ == '__main__':
    main()

import bz2, sys, curses
from itertools import zip_longest
from walt.client.term import TTYSettings

LOGO_DATA = bz2.decompress(b'BZh91AY&SY\xc9\x16Q\x9f\x00\x06\xb4ky\x00\x10\x00\x08\x7f\xe8\x00\x08\x00\x02\x7f\xe8\xc0\xfe\xff\x84\xf9\xef\x90\x00P\x03a\x83\xdc `\xa1\xa9\xe8\x80\xa4\xf57\xa8\x9e\xa3M2i\xea\x00\x19\x1e\xa7\xa83\xc9L5<D\xd2S@\x00\x00\x00\x00\x00\x01&\xa4(\xd0Se\x03A\xea\x1a\x01\x93Cz\xa7\x94\xd02\x18\r\x00\x00\r\x00\x00\x00\x00\x01&\x92\xa9\x1e\x93\x10\xd3&\x04\xc2210L\x13!\xa4\xc0\x03Eq\xa9o>\xb5S\xac\xa7\xf1F\x1d\xc4U\xb4j;\xd2\x89\x08 \xb0\x98\xa0\x0fs\x124\x83\x95\xc2^\t\x028=o-\xb2;\xb6\xbbo\xac1\xe1k\xd9\x81\xb4\xc4\x89\xe4\x97\xbe\x18\xafVz\xdf\xd17\xcaM\xc54\xde\xf61\xc7ySt\xa6\xa2\x80\xb1G"<\x89H\xdc\xa3a\xeed\xd1\xdb-\xc3\xa7K\xf2\xeaAbj\xcb\x0eb*a\xa0\x89\xe6Id\x97ds\x17\xef\xf1\xc6\x8e\x0b\x9d;H\x817s\xeb\xe1~\xb03\t\xf9\t\x070!@I\xd9G\x1eBQj,Z5M\x05\xc9.\x84gl\x02\x11\x03L\x16\x11\xe3\x07M\x18\x85\x84\x14\x90d\x16\x17\x121R\xa0r\x06\x01\x08\xc9\x84\x14\rT\xd5\x05%6\x81;e\xd7E\xcb\x16\x98F\xa9m\x0c\x01z\x97\xaaXbB\xa0\x10\x9a\x04EUt\xba\xb5\xb9@\xb0aU\x8b!\xe5$\x08i@!\x12\x10\xf2\x80B:5)MM]\x1a*\x0c\x05\x9a.\x89\x04\x19\xa9\x12]\xe4#l\xd4\xf3\x84\n1\x8c\n\x97&\x14\xe5\x92s\x85\x84\xb2\xb3aE^/\x12Zr[\x97z\xb6"\x06\x1aa\x1b\xcc\x06\xa5\x88\xb5HI\xdd\xc9\x99\x19F\x14\x06Q\xab\x08\x80\x85T\x936\x99Wl\x10\x9b\x8a5A\xb2M\x16\x93 \xc1W\x98\x98\xb1;\xe0\x01\xe8G\xe0\x1d\xf5B\xa1r\x80(b\x8c\x16T!P\xb9@\x85I\n\xc0\x91I\x0b\x86Dp\xb7\x1c\x90k\x15\xa4U\x8a\xa1X,L\xad\xb0r\xc0\xa8J\x91\xb40o\xac \x10\xb9\x99!%@\x00\xb3\x19\x8c&\x92\x17%\xcbB\xb2\xa2\xd1\xc1q\x15\\J\xcc\x91U`\xe3d\x05\x16\x18\xd7(X\xa1\x88\x06\xc1\xf68\xec\x03\xcd\x93\xad\r\xec\xbb\xac\xf5y\xd3\x0e\x97@\x92\x84\'fW\xb0\xa1\xde\xc3\xa2\xf5!\xefL+\'C\x03{,\xc5&\x1e\xadu\x0c\xd8u\xed\xa3\xe5TIt2H\xb3\xb9\x03s,\xc23\xba\x19\xa6[\xeaqa\x9aY\x0f\x07\x1a\x93B\x1cS\xf0\xcd\x9b\xa8&H\x1b\x10?\xd9P\xbb\x18aU\xbb\xfa\xd5G>\xba83w\x9b\x9a\xd1dY\x03k2\xef\xa0\xf5\xb9\xb0\xd6<\x1a\x10v\xd1\xcc\xda\xf5$\xbb93~\x8d\xb6\xc5\xe8\x0b\xa7B`\xaa0\xfe5 \x88(\xfbKE\x01Qg\xfc]\xc9\x14\xe1BC$YF|').decode('utf-8')
LOGO_WIDTH = 32

def try_add_logo(left_text):
    tty = TTYSettings()
    # verify if terminal seems to handle 256 colors at least
    if tty.num_colors < 256:
        return left_text    # failed, cannot add logo
    # try to encode logo with terminal encoding
    try:
        logo_lines = LOGO_DATA.encode(sys.stdout.encoding).splitlines()
    except UnicodeEncodeError:
        return left_text    # failed, cannot add logo
    # verify terminal is large enough
    text_lines = left_text.splitlines()
    max_text_len = max(len(l) for l in text_lines)
    if tty.cols < max_text_len + 3 + LOGO_WIDTH:
        return left_text    # failed, cannot add logo
    # ok, everything seems fine
    if len(logo_lines) > len(text_lines):
        text_lines = [ '' ] * (len(logo_lines) - len(text_lines)) + text_lines
    format_string = '%-' + str(max_text_len) + 's   %s\x1b[0m\n'
    out_text = ''
    for text_line, logo_line in zip_longest(text_lines, logo_lines, fillvalue=''):
        out_text += format_string % (text_line, logo_line)
    return out_text


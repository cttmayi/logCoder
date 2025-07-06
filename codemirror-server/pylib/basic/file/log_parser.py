import re



def _common_parser(lines, regex, header):
    rows = []
    pattern = re.compile(regex)
    for line in lines:
        match = pattern.match(line)
        if match:
            row = {header[i]: match.group(i+1) for i in range(len(header))}
            rows.append(row)
    return rows

PARSER_ANDROID_REGEX = r'(\d+-\d+) (\d+:\d+:\d+\.\d+) +(\d+) +(\d+) ([A-Z]) (.+?): (.*)'
PARSER_ANDROID_HEADER = ['date', 'time', 'pid', 'tid', 'level', 'tag', 'msg']
# 01-27 23:53:12.299   665 12258 W ratelimit: Single process limit 50/s drop 280 lines.
# 11-25 19:41:19.813  1153  1153 F libc    : Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid 1153 (init), pid 1153 (init)
# 03-17 16:13:38.859  2227  2227 D TextView: visible is system.time.showampm
def _android_parser(lines):
    return _common_parser(lines, PARSER_ANDROID_REGEX, PARSER_ANDROID_HEADER)



AUTO_PARSER = {}

def set_auto_parser(type, regex, parser_or_header):
    if isinstance(parser_or_header, list):
        header = parser_or_header
        parser = None
    else:
        parser = parser_or_header
        header = None

    AUTO_PARSER[regex] = {
        'parser': parser,
        'header': header,
        'type': type,
    }


def auto_parser(lines, match_count=3):
    for regex, attrs in AUTO_PARSER.items():
        pattern = re.compile(regex)
        count = 0
        for line in lines[:match_count*2]:
            match = pattern.match(line)
            if match:
                count += 1
        if count >= match_count:
            if attrs.get('parser') is not None:
                return attrs['parser'](lines), attrs['type']
            elif attrs.get('header') is not None:
                return _common_parser(lines, regex, attrs['header']), attrs['type']

    return None, None


set_auto_parser('android', PARSER_ANDROID_REGEX, PARSER_ANDROID_HEADER)


if __name__ == '__main__':
    lines = [
        '01-27 23:53:12.299   665 12258 W ratelimit: Single process limit 50/s drop 280 lines.',
        '11-25 19:41:19.813  1153  1153 F libc    : Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid 1153 (init), pid 1153 (init)',
        '03-17 16:13:38.859  2227  2227 D TextView: visible is system.time.showampm',
    ]

    # set_auto_parser('android', PARSER_ANDROID_REGEX, _android_parser)
    # set_auto_parser('android', PARSER_ANDROID_REGEX, ['date', 'time', 'pid', 'tid', 'level', 'tag', 'msg'])

    ls, t = auto_parser(lines)
    assert t == 'android'
    assert len(ls) == 3
    assert ls[0]['msg'] == 'Single process limit 50/s drop 280 lines.', f'{ls[0]}'
    assert ls[1]['msg'] == 'Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid 1153 (init), pid 1153 (init)', f'{ls[1]}'
    assert ls[2]['msg'] == 'visible is system.time.showampm', f'{ls[2]}'
    print('DONE')
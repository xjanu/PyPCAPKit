# -*- coding: utf-8 -*-
"""FTP Command"""

import csv
import re
from typing import TYPE_CHECKING

from pcapkit.vendor.default import Vendor

if TYPE_CHECKING:
    from typing import Callable, Optional

__all__ = ['Command']

#: Command type.
KIND = {
    'a': 'access control',
    'p': 'parameter setting',
    's': 'service execution',
}  # type: dict[str, str]

#: Conformance requirements.
CONF = {
    'm': 'mandatory to implement',
    'o': 'optional',
    'h': 'historic',
}  # type: dict[str, str]

#: Command entry template.
make = lambda cmmd, feat, desc, kind, conf, rfcs, cmmt: f'''\
    # {cmmt}
    {cmmd}=Info(
        name={cmmd!r},
        feat={feat!r},
        desc={desc!r},
        type={kind!r},
        conf={conf!r},
        note={rfcs!r},
    ),
'''.strip()  # type: Callable[[str, Optional[str], Optional[str], Optional[tuple[str, ...]], Optional[str], Optional[tuple[str, ...]], str], str]

#: Constant template of enumerate registry from IANA CSV.
LINE = lambda NAME, DOCS, INFO, MISS: f'''\
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""{DOCS}"""

from pcapkit.corekit.infoclass import Info

__all__ = ['{NAME}']


class defaultInfo(Info):
    """Extended :class:`~pcapkit.corekit.infoclass.Info` with default values."""

    def __getitem__(self, key: 'str') -> 'Info':
        """Missing keys as specified in :rfc:`3659`."""
        try:
            return super().__getitem__(key)
        except KeyError:
            return {MISS}


#: {DOCS}
{NAME} = defaultInfo(
    {INFO}
)
'''  # type: Callable[[str, str, str, str], str]


class Command(Vendor):
    """FTP Command"""

    #: Link to registry.
    LINK = 'https://www.iana.org/assignments/ftp-commands-extensions/ftp-commands-extensions-2.csv'

    def process(self, data: 'list[str]') -> 'tuple[dict[str, str], str]':  # type: ignore[override]
        """Process CSV data.

        Args:
            data: CSV data.

        Returns:
            Enumeration fields and missing fields.

        """
        reader = csv.reader(data)
        next(reader)  # header

        info = {}  # type: dict[str, str]
        for item in reader:
            cmmd = item[0].strip('+')
            feat = item[1] or None
            desc = re.sub(r'{.*}', r'', item[2]).strip() or None
            kind = tuple(KIND[s] for s in item[3].split('/') if s in KIND) or None
            conf = CONF.get(item[4].split()[0])

            temp = []  # type: list[str]
            rfcs_temp = []  # type: list[str]
            #for rfc in filter(lambda s: 'RFC' in s, re.split(r'\[|\]', item[5])):
            #    temp.append(f'[{rfc[:3]} {rfc[3:]}]')
            for rfc in filter(None, map(lambda s: s.strip(), re.split(r'\[|\]', item[5]))):
                if 'RFC' in rfc and re.match(r'\d+', rfc[3:]):
                    temp.append(f'[:rfc:`{rfc[3:]}`]')
                    rfcs_temp.append(f'{rfc[:3]} {rfc[3:]}')
                else:
                    temp.append(f'[{rfc}]'.replace('_', ' '))
            rfcs = tuple(rfcs_temp) or None
            cmmt = self.wrap_comment('%s %s' % (cmmd, ''.join(temp)))

            if cmmd == '-N/A-':
                MISS = '\n'.ljust(25).join(("Info(name='%s' % key,",
                                            f'feat={feat!r},',
                                            f'desc={desc!r},',
                                            f'type={kind!r},',
                                            f'conf={conf!r},',
                                            f'note={rfcs!r})'))
            else:
                info[cmmd] = make(cmmd, feat, desc, kind, conf, rfcs, cmmt)
        return info, MISS

    def context(self, data: 'list[str]') -> 'str':
        """Generate constant context.

        Args:
            data: CSV data.

        Returns:
            Constant context.

        """
        info, MISS = self.process(data)
        INFO = '\n    '.join(map(lambda s: s.strip(), info.values()))  # pylint: disable=dict-values-not-iterating
        return LINE(self.NAME, self.DOCS, INFO, MISS)


if __name__ == "__main__":
    Command()

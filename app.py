"""ちょこまな・しゃかい（ちり）の Streamlit アプリ。"""
from base64 import b64decode
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
from time import perf_counter
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from uuid import UUID, uuid5
from zlib import decompress

import streamlit as st
from streamlit.components.v1 import declare_component

# SVG輪郭（国土地理院「地球地図日本」由来）。詳しい出典はREADME.mdを参照。
MAP_DATA = (
    "eNqEve3Obkt2FXYv/Xtrq74/uIbuG2iUH05AgR8xEUl+RZFy2h2M7bbNlwMhdjoGDAYc4zZyiEwMF7N92u67yFNjjDlrrufd"
    "rUhHW+PUW6ueWrWq5vec9Vf/x+/8zb/2nb/ynZS/8+k7v/gL/81ff+Fvf/SPf/on/+Fn3/zDV9Pf/uu/8Nf+5i/+16/WL9/8"
    "xy/f/PMv3/zal29++OWbf/3lm7/z+vMv/OJ/9Tf+1t/+zl/5q633z3l+yql8HuO/+PSd//Jv/Q+/+Nf+u9cfat+f9/xU2+dc"
    "PpXXn9en/PqfVF+d/ttf+O//xmvk77Vymlv/3L57YP/U2ucBOD61itb6eX5q5XN+wdfDn1r+3K01fd7WanB/qvvzfMH+an1B"
    "PtY+1SX4mtDACP3AiZ8AXJ8T4DqtZ4TBx8oLzjMYR5hsTYD99D3zfXU7cANuwZpeb/GCr741nw7jjEDY1TrO+swLXzOr9fxa"
    "Q996fqKdSb7gOo+dDv1z1Vu8/k2azutl61mHF3yt52slx5lZe83kU1tnOq9/X2uGJXnBcWAFXAeuF9yv1p7OG5+GTx1L/fo3"
    "ferl9H39bR3I1vyp1/NrBl9v8fpb+9TbGezV8GodZ7DztwNf0zl75VNfgOM1344f7md9Rzqv2c+ivmAH3J9GPvMdZyVHPYOd"
    "hk+jnR8eZ8MMLMnrb6++40xynM/9hK9fe3Urn8bECOcLDbz8+ffTxJrNM/WJN37B/Wliy82zER2i9fWas53H6hl3rgOxf1c7"
    "fbF31nwt1MRr7rPB5z7j7vM1X/DVd59NO/Hyu7/GXVj1/Zqqwcm+G3Cd1gU4P62Mcc/qvOC0DvhC+3zjF9yA/dOqaN2vX3vB"
    "ZfBsrv46kS94pt7TOvCsWc/pPHa+W8/njV8d1gs29s2A7YzweiwPjtsBMYfz2PmamE7PGDej7zqPZbUCZsBpEDNLp0M5n/v1"
    "8uMFzyTPIr8g1ux8wl7ONsKq99cxfS1UQ+uZw8R0XmczX9j53Q7EJzyP4bsV/MSZzjw7quPwzrN/BTvGRYeOEQCxUBxsAnb7"
    "xge28xYDsPILnbeYZ81Oaz6t87zxC776LsFy4AZ8rcPGJNPpu9F6PsvOWpL5aeNblLMfXruGMyuf9tRbtAOnXvNsFeu7tFAO"
    "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"
    "dXKt6P7J6jMDTrJfVLk5iYfbFGqdbiupdUjymsA+jvpAggtFymu1GkgJOMumo30O20FlOALfq1bZgIr3GToXS+7Yc17M7Vqr"
    "+QY2zlRVkfJazVU8gYdcZbVmcYxtGFyior6C4eRcotakgvc8yyPgpuL0B2cVODeMb1GTivcnH7Opv7nDa1mS3EmL7BKAWoba"
    "X3MoXe0d9M2KplcVR4c2UIrGX6CT1cdM4k4L2LhQzVvjL+DkGobVdkrAPAsZ9Hl5nxH61zBmdRedtUctJ2o/S/Q/PbWlqEW9"
    "aVdX64raWNTSntrb7R+1vagFRu3QtcbIjfflxj/9P3/pp7/9+x+58e9/+eZ3v5q3ByWnYW1nfr85cw6qQsei9DlVeL/aw++F"
    "dUt2gQO7j6cG9tDMosYWNbmo4UXN76kRXk0xapBPzTJqnO+aaJH/ILkW26X9zLc989xLC3vsfX/Gffvcz3efP/d/PBfxvMRz"
    "dM9XPHfxPFbx7vl2fuO5juc90oEnfbh0I9KTQGci/XnQpSe9unQs0rdI9yI9jHQy0s8nXb30NtLhJ32+dDvS80jnI/1/8gXn"
    "F7i0qjJchto5+1A7f8NZNm791lj63Q3s8o/aIQMMrkmTVtS8nevQVCZ62rvggqxaTWPjOMs0+NpUAjo5Bg2p1Myg2XN9oAXW"
    "WlW2mpjaYQ+42ncZSd9uSsusvOAINXa1l2ghQJ0hw0slr2fAC7jb3Hhxh/ep9rvc53yXYuW1V8AbZ2SZJYOXdaAU9pGZp61P"
    "sXcfaOecKWOblnzaE7RqthfghXNaVWtYcjvfnWdclg9Y5VFDv+atPpT5re6w+NHI0guuBWXqXZLxi2G6Bi0o1DWyrb9wlhWz"
    "2/yzfescrDXRcnMtOtHSU3+OZShajKIlKVqYouUpWqSipSpasIJlK1q8HpawaCGLlrNoUYuWtiYLXMxTzyn4af7Tv/jZv/yD"
    "j/zu773Y3NedNOem4MV9NR/87mgxmvTRFT6PI41+Xg/dsyXR2Nc74vLMihpaRyItRp9RDl+0tA7R2AJcvb2HPl19zrOg7bwE"
    "DDWrKsNwK/c8eBMutzzz78ANe3t5O/YJb2cmr+H4qJcGqmV6aJ3iUw14YP9v4Aw8gHkuir1jwX7AJXjifbjkU+flBLxan8Yz"
    "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"
    "buwl3/PMUxNeijYujpfmsH3Nl+cT2ZhT4yw/X0lj1vBbCTj2GX7uLDo5Yf9nW9uRPeK8jHy/EYug6VlLie3eZ+p8WQptGTc5"
    "wPDAmEX0pHt/yBLDUmU55vL2okg7zmcq6u7iOzfDQzlf9i5dYzZFmZdhOV8NmNF70+fZNf87B4t0T0ZnEKFeRvModsPW3vzZ"
    "pnEOjer6rQ7c/b0sfXUAWzRhYbQocuWK8gqrniXdTt4HNHx0LxNRFFVfRGOzchsLo2k7aSZ5EPgLI2XJFxwP78/ftfTe5H2a"
    "xlzGd8a6vIOR0+RNov98dquExfI+VbyDcx4BF+/POfN8ZfVpxn8ZuY6i/IXF4xr3HnNI+X2tpEmxdaOswoKkregdm8rDlDGv"
    "XKQyUZCXVDCOZ8rKPlXgqeJxj3aVg5riszX02SoQXLyIMPsnU3QZLHpcr1G+3Y87aX/6z37/591J+29gjf0YFPp6bx2fZ1Do"
    "cYCxRE8/QZGf53HXf35cKFdZPKbJhcxiMF4alIV+alcxmOrtjInoKh6UrGyp4y1JkK5fFXSpVlTGy6Z5+/SCRFlFYhg/lSzD"
    "uJVbnMYLEvW3okXPYka3yFEsfhSLIsViSbGI0jMrulqmcsz2i1mAj+zAmDUYswmfWYaedfqIN37GIcf45Bi3fOOZY5xzFTdY"
    "b3HRMV46xlGH+OoYd/2I056SvLpiUhTjzVg55l8wJm6E0nwsqtFMCvNvDalN5fUYU1xD7gnLxjLumKVxGTfOkrOMI+a+Yhxx"
    "nSoisiyujfG/enbfsrQsRsJ4N8aw1HGL33DPO67evyrXYAA3yxeoRfHwVWEZiu2vRfNkuMkC7gpPOX0Yi7Qs5p8xSsNi3Nie"
    "vb15GIrWtoRYeuEs3KygCGPo+r5jMtesbJc+1J95YRy/Wzxdsv0pjO9ejMNsi8Xjlcxl3uzzsnSFygi4KkRGlQOKaYFVIRoq"
    "wlSz6MAKFLGE0s0/+63/8LNf/srFQcgT/OYPv0IOy+slWMivP4sbHuM/g0tzPuW1+jwx8v0RWcFyx4qRtHLW7S2OMsZXhrjL"
    "GI/5iNOM8ZsxrvMZ73njQGN8KPvs91LJsYTyo7RyLLm8Qp+pKwnmW7nmZxnnWN75ln2O5aCfZaJv+ehYVvpjuemu2NJtURyP"
    "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"
    "t7PPsgsf6JueLfRpqr/S3nBXVe9tl0swAm6O67PmpRmqS2aVv3mRRXdsNbgqLsToVh2cKfccfyX91kIBXF6SVFD0NtvFPKte"
    "X/aytW1WGLfDhr/sas6GIrnVasOsftd5saIw24d8/QvYLwpa9OPgbK6pGICBPn7h0ANP1TTjOH45k7dX4GaXGK2l60c7cAJu"
    "wBV7j5h+9jMf+oO62nlhUvVxwOLXupcqralYiBZw9XexPsXxCP05/6p3yeYD4roJd9W3WFjzZZc8rabxK7Bf/rTsyr8EzEuk"
    "hn3rBjaxsi6jysArtBcfM4XfSro6cGEvbXsX1sTib01732yXqHCcafEhxS5RaXZxSvdxuvoMu1CFl1SxfANjSGZXrY7sfXiZ"
    "TFccBS+f6fZ9563tofNIOsNzqvG5Vln1Er0mEC/PaUmX3jTzkbFWB/2erOdBesgzTho7Wftk3EtghLtidVZoX/bu9LH6s+2t"
    "fSiOgvTByjfUOUKfLjrP9fE4jdkv3VZ5CLZzTPCmuWRn2/at6bNTqQjirNIP3CcJz3L/eI0i1jajHW9V8cHs7danG0/3kiXZ"
    "zgV9dmvKlzdx1pbx5bXVfwPTzsmzRjtns7NGfxbrvhTStCnfk9ONPPVbw2zIK1RjUP9+z2mGGM/xacJiwfG0Lo1KS2fWKxgs"
    "85v4u6clWprMbLKKTATT1pPmI55Hmp6WmcuSrT/NVvxGuYjO0yafce5YH6g7bmqnTb4FXIzvZDuPCX63ahc90QfHC4vyEI9L"
    "toaT1TCGztFEu19klO0Cq2x+PdYvzVan9LZDhtGz6drtWV80Wz3S8uY3jP7Ep5/R/Y/RL/nwV0Y/ZvRvRr9n9IdGP2n0n0a/"
    "avS3Rj/s0z8b/bbRn3v9vB/9v1l9rr84+pGjfzn6nb/mj84f/NfRr3393U8/+PWPR7+5+9Oj+hAvWvnh//4XP/69j+rDD5BC"
    "9Ltfq9byIrqk4as/q7V02OXPYh3T9Ym3PM6nh/W9ajnHm5XoaT26VqVobYpWqGidelqtojUrWrmi9WsHy9m1lkUrWrSuRatb"
    "tMbZ3XLbMtG5hR8Wvmj5ixbBaCmMFsRoWYwWx6cl8looo+UyWjSfls6t+cMJY3P7iqvcno2u9evGj6746KKPrvvo0o+u/hgC"
    "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"
    "/NmkTTMtZQabSc+WfVOiiqUxLttkjoulKbFeGU143GQ0QVZLAyx6F2tnCtKg+t2CtGLFzoppCZQ+VJRwXHukJCOTpKZpBm/9"
    "d2hfFtawLCQi+W91/a6HQZz5vCZX6hWfxAqnyJSLW2K7U6y52EC8oYI/zBsqOKESXlLsm2M2iWQr9OnOvjkhGiWWBXtMlylH"
    "kCnHo725vGvtZ9l5N4bPwmpWioBRCC3di8FY//GsgRVvGv29v/uXv/Lvvnav3g9+5Sva/4nnpF08v4XJ8lK9w6YzwmRPlOx+"
    "REk9zP1PD2/0/EaPsHuKowf54VmOHuenJ/p6qKPnOnq0o6f76QGPnvHrMY+e9Ohhn15f9OmFj9756LV/hr7HkPgbKv8Mof//"
    "D7mPIfrP0P0b0h9D/Z8pAO4aiSkDj1SCZ4pBTD24KQkxVSGmMDxTG27KQ0iFiCkSb6kTN6UipFq8pWDE1IyYsuGpHG8pHjH1"
    "I6aExFSRmEISU0s+ppzMDykqMXWlvGFLdbkpMDE1JqbMPFNpborNUGrbtnSnxBuMm1LMiqcLJUV+TkvdUupTVvtNKYqpRkUp"
    "XSWkO9WQ1tTf0p1iGlRRn6QIVUtlAk9kO864xgQdOH3M5aY54LZ2pYb1cVOuOtO+iqKSkvfpmv+WO1O/27vevfmzSTfMN+Bi"
    "mOvJMRNdCB176UaM6Bt1plLSDcBURGKm/oFod0urZESHp1J2pnk2zTNbaqd+t8rVSmwuWMkSPaSg9nFTX/u86bF93bRWri33"
    "P26bVzmCbinww1yklA3kCt3XpSrX5tR5HG/uz6dbNLpLoxs1ulev2/Xpjr0upei+fbp1r7s3uoGje/jpNpYSG/heDffJfvsP"
    "fvTT/+tH3/7kJx8v2f7NE5agq7Y/MMATDHh22ms9n3HCNLmeFeu6Y/vIco80EYbU7akNcv3Fz8W+HyF+nPjRrHZC/Mj8sNsE"
    "zMdGiBskbpznhoobLW7AuzHjho0b+bnB48aPB6KHQ3MPUDxY8cDFg/g8oPfgxgP9POiRAIxASCLBiITkEphIeCJBioQqELBI"
    "2B4ELxLColzP+ZZjGnNPY07qM1f15rDG3NZn/uvNi435ss882optu/xZhucbvn0Mv36rpEefafMpSYJSBebcXu9esvoXtFsI"
    "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"
    "fibP/yT7pWR/lezHkv1bst/Lpz/M85PJ/jPZryb722Q/nOSfk/12Pvx5sp9P9v/JfkGf/kLPjyj7F336HT1/pOyn9Om/9Pya"
    "sr/Tpx/U84/KflPZnyr7WWX/q+yX9emv9aMf16Rv2PP7+vQHy35iz38s+5V9+pvRD+1b/kb8gwfimDNKIODGGPlfY3NEAI0x"
    "dqLSYD/JXIAJofLxNhQEVvIAGJEwGxslgmAMgZtFTgDvYJgMLG7RB1+oc6XDaXOTQvk7eFZqZ/G5cDhYOmjhZICDGZMYmxcY"
    "NHB4TwVAt4RLHDz47WZQUfHfvvFRcmg5MSBQSfU76xsDnh6+H8aTpCFbspH+YbATiHqeCVfH8yeMgRikgtADVN4YSY3VqU5s"
    "RnLpJRF19bBF+5UnbUsSxPwJY5VjUHpIDVrxNSaQ6hyezLf8SRCNEsSJCQrs/Yx2Vjy3EyNCDZLO0kRfhb89vrvUhEuqr+zW"
    "kpKGm6EiFThcMnqIXjvCvSxSikOk7CHmnSfaRdp0uHAozN62+JoKxVdPHX7tXzvy0N+7nEijaJCj7DspZxSZ8iH3wNx/5Pdg"
    "IR/vJ0/sndrc9Gk7MLwdraXduZ6LLJbskILIphw0ILjtFzjGi+ldS3fjqU8KnTVJgIpewwk1YsG1J2nPHlFwDw+vg01lYbhG"
    "GootkYvDMjmM7wq0g2PiXldw7ekJH7mD3KvLnQjgDfD7d+DCPZ4rhTnSK2Xz/ROuPB8kmw+W97groL7yuu/74MV9d9FZSJ1Y"
    "JEooMTPxgK2ldYdlMLKwxY0Ls0KRfyWwPHje0E1F+F3NjfGPcGk56+kHeW0Vd1e4k6MhZlSd1BVawhQD72s2rmqLu0xNd5lG"
    "H62lnYh50jGOTeV3qo0IHoVTGseLGGfc5NhBoOF2cnsx38YduPCk5f62Jvclw2oJ19CtMMsldQ1XRU9X18Fl17PmKmWU/eXf"
    "/Jtf/uyf/UwYAoPzn//ut3/5K5qrCD7tH4RZdgPUIInN78H6fvT1Ifi90bPi6sNJMztvZqfOT2fP7ASanUOz02h2Jn1Optn5"
    "9NMp9TmrZifWT+dWS46xzxn200n2Oc9mp9pPZ9vshJudc7PTbnbmfU6+2fn30yk4tqvsRPyDc/FzOs7OyNlJOTsvZ6fm7Oyc"
    "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"
    "Ducr7chfeOtej9+CC0XjiOEiUDmqw2qkMb64MRr24kWt7qvfgJ1Hb3l36xdhBfl493fvUB5EKYahPnj7BUHbnlv7w+aXHrm4"
    "D2t0ZT9xGXIFlWHaN+7kSp+oTb1pr2vc4JRz3t0Esfu4YwH2L9WFi0F3er/vNeI+MU7vNzzs3en9hvMDOL3d8OBlVhioMB1u"
    "3pNv9Lun5/j+fi6benKN4ZQVkEsupZPX6NJ7SPdSpL1pT9nRIZVRXZL9VNbzU/nbv/qLv/s//+hXQ5D/9GZ7/8M/+9lJZd54"
    "qo0t+TPP+/WYgMRd6m9sO9HdTYJxkpvK7K7yXU6yinjkq4T6xn6oLudsRSzq8qxAXerx5eVQjx8vh3ocdY7XuWllfIkvpEBx"
    "38Pl1xH46q7B374+dB41eO7iGaa+feLjuDqO/rukcLFmlbD5b3HUe6oXxOS6eWLCnwh14KOKOvQVvbvLpG+p6kwKMxM+Sm7y"
    "mPQn9TFpi+aS5rhT8BB2ysMmc/B0XCmRXFwoec3W6b7SUvlxLP/HifggN+tM+Ht6hq8Jf1JPmSXsl0/4XrmGfcIn1FXs91kn"
    "6nf6vaKfRjeYW95ogr940CR9MVwIbjtY4Mg91MLXldj1WLPJxAw8aWIWxpg3mpXN2y9Rp7P+UD9ZRyaz+9tKM1l33Gkmm4gx"
    "ORhzo0m6O67x28J2zPHy9lfUcbbOKAc+0efn9jPp9lN8fArHZHs7MM+hPxbjY2Gy57P2YZ1Bs/6Ez50nELvvZXTJ4Dty/CEq"
    "b45t9e+F8kY/aP22c6x6wroA6Ns1zocS87aHC5bmhifZ4vysnFeN7hCaY1gjM9WZXDsl5iewXL+64xrrdHFtYk2tqLN5S5iO"
    "cUpgrTXtD/Ch9jOFa2dtrrVNMZTrYm2utUV3ONVZXF+dLnPsD8t9vS+M82b5VN/W5j4DGR77T6XUzH3JpeKHu+9dLXBhf7Dv"
    "mePvg314oMTwoOLR/ZBxJtfhwQLDg5NdQHTxYgm7sOLypmNzXLzOcDwpurCOyy7DSRNe+aH0MjxAYHhAnUugFHAePt6fEr/t"
    "/O30ckhBw8uvyLRS/cU+o7yl8oyL4/usyTa7Y3O8ArtE5EH1wwNJ1I6Pm6c3Hh5sMjw4n2PL9jefNRz3hLf3/9bxyx3xpiTY"
    "HI8Yn81vMdUOv4WLHvd7fX/UoQ/2/QOP3h4eATkGPowPukfG82EDH8lfhnUm6xfH1evj5ZdjlDfHt9PDyxvxcVwdt2hn8FnT"
    "8YjnTpbvaMcV84FvnXvLcdHLcXE8HXfH9108RyDLPYvgcCnN2SYubq6YX46P4+14e53h2Py3PX7bvM7ns4CPY7xX935iPKvj"
    "pQk6Oj9wc4zx398facG64R8J2h3nhB8wfDm1iMp9pkBF5GTxA4bKwEbl94BqyJXiwj6IrH+P+wErKMsPFe0j2mlsp/EqOjwX"
    "G6wnqt/525ba2f5cS/i7HGY1J34fnmpnOH3KgMna2e7HhjLeJ+iGMt5XM6zAF//B70/QLEHOAC2TK6Qm+ITcDXdaDdfACQ4h"
    "d92bJjfcV9/3WdBFXlnnkpi7DQo6M9idoFUDYRYUc+BmhW4P/EvQ6KFzSA8HO1Vxo9iAvQWbhzshD89C5S/u+HuuuHe/sOt8"
    "7ny688Olf37Lkb6ZLwI3lAwoNPn9fII7/c2AdvMaSr7HrklHY5Kb1qJ8VBhnpTqTstiWTN2kqCm3oUV/kvn1cJFQOjcP0051"
    "+MWH6vmLG9XhPJSn872PibVype0xBw2Ey7E5bo6nL5VbB5uwHzpz0rjYU/nlHq+dXqvfxyPCRdzrcCKMGyISvMshQtZO0RJ1"
    "4JnY8crm7jeQAYZjyAZGK4fOcZUDr3u2+lfzAE+eU07WoLN18JwajpefI9XxDjz99o2ZCtU4nfjc5g/WLDgeYGYfP9UlAk1e"
    "JVqI6ItTvoYIBLF/hzZXV5LpX+djEk5uNNMnpCxxYw2aS83xwEZzjyH3qenYZn1dOEmAq4gkc3hg6nCS+//4P/1P/qP/H6Mx"
    "2yk="
)

SOURCE = "geography"
LEGACY_VERSION = "geography-prefectures-1"
MAP = json.loads(decompress(b64decode(MAP_DATA)))
PREFECTURES = {p["id"]: p for p in MAP}
REGIONS = [
    ("north", "ほっかいどう・とうほく", 1, 7),
    ("kanto", "かんとう", 8, 14),
    ("chubu", "ちゅうぶ", 15, 23),
    ("kinki", "きんき", 24, 30),
    ("chugoku", "ちゅうごく", 31, 35),
    ("shikoku", "しこく", 36, 39),
    ("kyushu", "きゅうしゅう・おきなわ", 40, 47),
    ("all", "ぜんこく47とどうふけん", 1, 47),
]
LEGACY_MENUS = {
    f"geography.prefecture.{code}": {
        "menu_id": f"geography.prefecture.{code}", "category_id": code,
        "label": name, "category_label": name, "difficulty_id": "puzzle",
        "difficulty_order": 1, "progression_group_id": f"geography.{code}",
        "skill_ids": ["geography.prefecture.location_name"],
        "prefectures": [f"{i:02}" for i in range(lo, hi + 1)],
        "mode_options": ["challenge"], "assessment_method": "automatic",
        "estimated_duration_ms": (hi - lo + 1) * 40_000, "duration_basis": "provisional",
        "question_count_default": hi - lo + 1, "planned_question_count": hi - lo + 1,
        "supports_direct_launch": True, "is_active": True, "next_menu_ids": [],
        "selection_instructions": ["ピースを日本地図にはめる", "都道府県の名前をえらぶ"],
    }
    for code, name, lo, hi in REGIONS
}


def iso(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse(value):
    if not isinstance(value, str) or len(value) > 32:
        raise ValueError("invalid timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("missing timezone")
    return result.astimezone(timezone.utc)


def medal_grade(correct, total):
    if total <= 10:
        return ("gold", "silver", "bronze")[total - correct] if total - correct <= 2 else "white"
    return next((name for name, pct in (("gold", 90), ("silver", 80), ("bronze", 70))
                 if correct * 100 >= total * pct), "white")


def build_legacy_records(raw, profile, assignment=None, now=None):
    attempt = UUID(raw["id"])
    if attempt.version != 4:
        raise ValueError("invalid attempt")
    menu = LEGACY_MENUS[raw["menu"]]
    started, ended = parse(raw["started"]), parse(raw["ended"])
    now = now or datetime.now(timezone.utc)
    if ended < started or ended > now + timedelta(minutes=5):
        raise ValueError("invalid attempt time")
    status = raw["status"]
    questions = raw["questions"]
    total = menu["question_count_default"]
    if (status not in ("completed", "abandoned") or not isinstance(questions, list)
            or len(questions) > total or (status == "completed" and len(questions) != total)):
        raise ValueError("invalid completion")
    records = []

    def add(kind, at, payload, *, question=None, occurrence=None, segment=None):
        records.append((at, kind, payload, question, occurrence, segment))

    plan_id = None
    if raw.get("assignment") and assignment and assignment["plan_item_id"] == raw["assignment"]:
        if assignment["menu_id"] == menu["menu_id"] and assignment["content_version"] == LEGACY_VERSION:
            plan_id = assignment["plan_item_id"]
    start = dict(menu_id=menu["menu_id"], category_id=menu["category_id"],
                 difficulty_id=menu["difficulty_id"], mode="challenge",
                 planned_question_count=total, settings_snapshot={"activity": "map_and_name"})
    if plan_id:
        start["plan_item_id"] = plan_id
    add("session_started", started, start)
    seen = set()
    correct = answered = 0
    previous = started
    for index, item in enumerate(questions):
        ident = item["id"]
        if ident not in menu["prefectures"] or ident in seen:
            raise ValueError("invalid prefecture")
        seen.add(ident)
        at = parse(item["shown"])
        if not previous <= at <= ended:
            raise ValueError("invalid item time")
        qid = f"geography.prefecture.{ident}"
        item_kwargs = {"question": qid, "occurrence": str(uuid5(attempt, f"item:{ident}"))}
        options = item["options"]
        if len(options) != 4 or len(set(options)) != 4 or ident not in options or not set(options) <= PREFECTURES.keys():
            raise ValueError("invalid options")
        add("item_presented", at, dict(presentation_kind="first", parent_occurrence_id=None,
            order=index+1, answer_exposed_before=False, choice_order=options), **item_kwargs)
        placements = []
        hinted = False
        regional_zoom = False
        choice = item.get("choice")
        actions = item["actions"]
        if len(actions) > 120:
            raise ValueError("too many item actions")
        for action in actions:
            stamp = parse(action["at"])
            if not at <= stamp <= ended:
                raise ValueError("invalid activity time")
            at = stamp
            if action["type"] == "hint" and not hinted:
                hinted = True
                add("support_used", at, {"support_type": "hint", "hint_step": 1}, **item_kwargs)
            elif action["type"] == "zoom":
                regional_zoom = menu["category_id"] == "all"
                add("learning_activity", at, {"activity": "map_zoom"}, **item_kwargs)
            elif action["type"] == "placement" and ident not in placements:
                target = action.get("target")
                if target is not None and target not in PREFECTURES:
                    raise ValueError("invalid placement")
                placements.append(target)
                add("learning_activity", at, {"activity": "map_placement", "selected_prefecture_id": target,
                    "placement_index": len(placements), "is_correct": target == ident}, **item_kwargs)
            else:
                raise ValueError("invalid activity")
        if choice is not None:
            if choice not in options or not placements or placements[-1] != ident:
                raise ValueError("invalid answer")
            stamp = parse(item["answered"])
            if not at <= stamp <= ended:
                raise ValueError("invalid answer time")
            at = stamp
            used_help = hinted or regional_zoom
            right = choice == ident and placements[0] == ident and not used_help
            correct += int(right)
            answered += 1
            add("response_submitted", at, dict(response_index=1, response_status="answered",
                assessment_method="automatic", is_correct=right, input_method="map_and_choice",
                response_value={"choice_id": choice, "name_correct": choice == ident,
                                "first_placement_correct": placements[0] == ident},
                support_before_response={"hint_count": int(used_help), "explanation_seen": False,
                    "answer_seen": False, "worked_example_seen": False, "parent_help": False},
                answer_latency_ms=int((at-parse(item["shown"])).total_seconds()*1000)), **item_kwargs)
        elif status == "completed" or index != len(questions) - 1:
            raise ValueError("missing answer")
        previous = at
    intervals = raw["intervals"]
    if not isinstance(intervals, list) or len(intervals) > 500:
        raise ValueError("invalid interval count")
    previous = started
    for index, pair in enumerate(intervals):
        lo, hi = map(parse, pair)
        ms = round((hi-lo).total_seconds()*1000)
        if not previous <= lo < hi <= ended or ms > 180_000:
            raise ValueError("invalid interval")
        previous = hi
        add("time_interval_closed", hi, dict(start_at=iso(lo), end_at=iso(hi), active_ms=ms,
            timing_quality="complete", phase="other"), segment=str(uuid5(attempt, f"interval:{index}")))
    add("session_ended", ended, dict(status=status, answered_count=answered, first_correct_count=correct))
    events = []
    for sequence, (when, kind, payload, question, occurrence, segment) in enumerate(
            sorted(records, key=lambda row: row[0]), start=1):
        event = dict(schema_version=1, source_app=SOURCE, profile_id=profile,
            attempt_id=str(attempt), event_id=str(uuid5(attempt, f"event:{sequence}")),
            app_version="1.0.0", content_version=LEGACY_VERSION, event_type=kind,
            occurred_at=iso(when), sequence=sequence, question_id=question,
            occurrence_id=occurrence, segment_id=segment, payload=payload)
        event["event_hash"] = hashlib.sha256(json.dumps(event, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        events.append(event)
    medal = None
    if status == "completed":
        medal = dict(source_app=SOURCE, profile_id=profile, attempt_id=str(attempt),
            category_key=menu["category_id"], category_label=menu["label"], stamp_char="地",
            reading="ち", difficulty="puzzle", correct_count=correct, total_count=total,
            grade=medal_grade(correct, total), finished_at=iso(ended))
    return events, medal

PREFECTURE_DATA = """
01|札幌市|さっぽろし|根釧台地|こんせんだいち|台地|43.39,144.79|酪農|らくのう|夏でもすずしい道東の気候|広い土地を牧草地にして、牛のえさを育てる|日本の北にある北海道。その東の根釧台地は夏もすずしく、広い土地が牧草地に使われています。牧草を牛のえさにして、乳牛を飼う酪農が行われています。
02|青森市|あおもりし|津軽平野|つがるへいや|平野|40.73,140.42|りんご栽培|りんごさいばい|津軽のすずしい気候|平野のまわりにも果樹園をつくる|津軽地方では、すずしい気候のもと、平野のまわりなどに果樹園が広がり、りんごが作られています。
03|盛岡市|もりおかし|北上川|きたかみがわ|川|39.38,141.13|米づくり|こめづくり|川にそって平らな土地がある|用水路で田に水を引く|北上川にそった平らな土地に田が広がり、川などから用水路で水を引いて米を作ります。
04|仙台市|せんだいし|仙台平野|せんだいへいや|平野|38.25,140.98|米づくり|こめづくり|海の近くまで平らな土地が広がる|水をためられる田を広くつくる|太平洋に面する仙台平野には平らな土地が広がり、水を引いて田を作ることができます。
05|秋田市|あきたし|横手盆地|よこてぼんち|盆地|39.32,140.47|米づくり|こめづくり|山に囲まれた盆地の底に平らな土地がある|盆地の平地に田をつくり、水を引く|横手盆地では、まわりを山に囲まれた平らな土地に田が広がり、水を引いて米を育てます。
06|山形市|やまがたし|山形盆地|やまがたぼんち|盆地|38.36,140.32|さくらんぼ栽培|さくらんぼさいばい|盆地のふちに水はけのよい土地がある|ふちの斜面などを果樹園にする|山形盆地のふちには水はけのよい土地があり、さくらんぼを育てる果樹園があります。
07|福島市|ふくしまし|福島盆地|ふくしまぼんち|盆地|37.80,140.44|もも栽培|ももさいばい|盆地のふちに日当たりのよい斜面がある|斜面などを果樹園にする|福島盆地のふちの日当たりのよい斜面などに果樹園が広がっています。県内では、盆地の周りに加え、須賀川市や会津美里町にもももの産地があります。
08|水戸市|みとし|霞ヶ浦|かすみがうら|湖|36.04,140.37|れんこん栽培|れんこんさいばい|湖のまわりに水を使いやすい平地がある|水を張った畑でれんこんを育てる|霞ヶ浦のまわりでは、水を張った畑で、れんこんになるハスを育てています。
09|宇都宮市|うつのみやし|那須高原|なすこうげん|高原|37.06,140.01|酪農|らくのう|高原は夏も比較的すずしい|牧草を育てて乳牛を飼う|那須の高原などでは、すずしい環境を生かして牧草を育て、乳牛を飼うところがあります。
10|前橋市|まえばしし|嬬恋高原|つまごいこうげん|高原|36.53,138.49|キャベツ栽培|きゃべつさいばい|標高が高く、夏も比較的すずしい|高原の畑で夏にキャベツを育てる|嬬恋村では、標高が高く夏もすずしい気候を生かし、夏に収穫するキャベツを育てます。
11|さいたま市|さいたまし|利根川|とねがわ|川|36.23,139.26|ねぎ栽培|ねぎさいばい|深谷付近の川沿いに畑をつくれる平地がある|水はけのよい畑で育てる|利根川に近い深谷には、ねぎを育てる畑があります。水はけのよい土は、ねぎの栽培に向いています。
12|千葉市|ちばし|九十九里浜|くじゅうくりはま|海岸|35.59,140.48|いわし漁|いわしりょう|太平洋に面した長い海岸がある|港を拠点に、沖へ船を出して魚をとる|九十九里浜は太平洋に面しています。近くの港を拠点に、沖でいわしなどをとる漁業が行われてきました。
13|新宿区|しんじゅくく|狭山丘陵|さやまきゅうりょう|丘陵|35.77,139.39|東京狭山茶|とうきょうさやまちゃ|丘陵のまわりに畑がある|木の葉を摘み、加工してお茶にする|瑞穂町など、狭山丘陵に近い地域の畑では茶の木を育て、摘み取った葉をお茶に加工します。
14|横浜市|よこはまし|相模湾|さがみわん|湾|35.26,139.43|しらす漁|しらすりょう|相模湾に面した沿岸がある|海岸近くの海で船を使い、しらすをとる|相模湾の沿岸では、海岸近くを泳ぐしらすを、船から網を使ってとります。
15|新潟市|にいがたし|越後平野|えちごへいや|平野|37.67,139.01|米づくり|こめづくり|信濃川などが流れる広い平野がある|水路や排水の仕組みを整えて田をつくる|越後平野では、広く平らな土地に水路や排水の仕組みを整え、田をつくって米を育てています。
16|富山市|とやまし|砺波平野|となみへいや|平野|36.63,136.97|米づくり|こめづくり|庄川が山から平野へ流れ出る|用水路を使って田に水を届ける|砺波平野では、庄川から取り入れた水などを用水路で田に運び、米を育てています。
17|金沢市|かなざわし|河北潟|かほくがた|湖|36.66,136.67|れんこん栽培|れんこんさいばい|潟の近くに水が使える低い土地がある|水田を利用した畑でハスを育てる|河北潟周辺を含む金沢の一部では、水を使う畑でハスを育て、加賀れんこんを収穫します。
18|福井市|ふくいし|越前海岸|えちぜんかいがん|海岸|35.91,135.95|越前がに漁|えちぜんがにりょう|日本海に面し、沖に深い海がある|港から沖へ出て、海底近くのかにをとる|越前海岸などの漁港から日本海へ出て、海底近くにすむズワイガニをとります。
19|甲府市|こうふし|甲府盆地|こうふぼんち|盆地|35.64,138.65|ぶどう栽培|ぶどうさいばい|盆地に日当たりや水はけのよい場所がある|盆地のふちなどに果樹園をつくる|甲府盆地のふちなどでは、日当たりと水はけのよい場所を使い、ぶどうを育てます。
20|長野市|ながのし|千曲川|ちくまがわ|川|35.98,138.56|レタス栽培|れたすさいばい|千曲川上流の高い土地は夏も比較的すずしい|高原の畑で夏にレタスを育てる|千曲川上流の川上村では、高い土地のすずしさを生かして、夏に出荷するレタスを育てます。
21|岐阜市|ぎふし|長良川|ながらがわ|川|35.44,136.78|あゆ漁・鵜飼|あゆりょう・うかい|あゆがすむ川が流れる|川であゆをとり、鵜飼の伝統を残す|長良川にはあゆがすみます。岐阜市では鵜という鳥で魚をとる鵜飼が伝統として続いています。
22|静岡市|しずおかし|牧之原台地|まきのはらだいち|台地|34.82,138.14|茶の栽培|ちゃのさいばい|広く、水はけがよい台地がある|台地に茶畑を広げる|牧之原台地の水はけのよい土地には茶畑が広がり、茶の葉を摘んで加工します。
23|名古屋市|なごやし|渥美半島|あつみはんとう|半島|34.65,137.19|メロン栽培|めろんさいばい|海に囲まれた、比較的あたたかい半島がある|温室で温度などを調整して作物を育てる|渥美半島では比較的あたたかい気候を生かし、温室で温度などを調整してメロンを育てます。
24|津市|つし|英虞湾|あごわん|湾|34.31,136.81|真珠の養殖|しんじゅのようしょく|海岸が入り組み、湾の内側では波が比較的おだやか|いかだなどから貝をつるして育てる|英虞湾では、おだやかな海を利用し、貝を育てて真珠を作ります。
25|大津市|おおつし|琵琶湖|びわこ|湖|35.23,136.08|湖の漁・ふなずし|みずうみのりょう・ふなずし|淡水の湖にフナなどの魚がすむ|湖で魚をとり、加工して保存する|琵琶湖の魚を塩と米で発酵させて保存する工夫から、ふなずしが伝わっています。
26|京都市|きょうとし|宇治川|うじがわ|川|34.89,135.82|宇治茶|うじちゃ|宇治川近くの山あいに傾いた畑がある|茶の木を畑で育て、葉を加工する|宇治やその周辺の山あいの畑では茶の木を育て、葉を摘んで加工します。
27|大阪市|おおさかし|大阪平野|おおさかへいや|平野|34.62,135.59|八尾若ごぼう|やおわかごぼう|平野に野菜を育てる畑がある|市街地に近い畑でも野菜を育てる|大阪平野の八尾では、市街地に近い畑でも野菜が作られ、八尾若ごぼうが知られています。
28|神戸市|こうべし|淡路島|あわじしま|島|34.32,134.83|たまねぎ栽培|たまねぎさいばい|瀬戸内海にある比較的あたたかい島|平地の田畑を季節ごとに使う|淡路島の南部では、比較的あたたかい気候のもと、米を作った田などで、たまねぎを育てることがあります。
29|奈良市|ならし|吉野川|よしのがわ|川|34.35,135.68|かき栽培|かきさいばい|吉野川近くの山の斜面に日当たりのよい所がある|斜面などを果樹園にする|吉野川沿いの五條では、山の斜面などにある果樹園で、かきを育てています。
30|和歌山市|わかやまし|有田川|ありだがわ|川|34.08,135.22|みかん栽培|みかんさいばい|川のまわりの山に日当たりのよい斜面がある|斜面に段々畑をつくる|有田川の周辺では、日当たりのよい斜面などに段々畑をつくり、みかんを育てます。
31|鳥取市|とっとりし|鳥取砂丘|とっとりさきゅう|砂丘|35.54,134.24|らっきょう栽培|らっきょうさいばい|海岸近くに水はけのよい砂地がある|砂地を畑にし、水を補いながら育てる|鳥取砂丘の近くでは、水はけのよい砂地を畑にして、必要な水を補いながららっきょうを育てます。
32|松江市|まつえし|宍道湖|しんじこ|湖|35.45,132.93|しじみ漁|しじみりょう|湖で川の水と海の水が混じる|湖底にすむしじみをとる|宍道湖は川の水と海の水が混じる湖で、その環境にすむヤマトシジミをとります。
33|岡山市|おかやまし|岡山平野|おかやまへいや|平野|34.65,133.92|白桃の栽培|はくとうのさいばい|平野の周辺に日当たりのよい土地がある|果樹園で桃を育てる|岡山平野の周辺など、日当たりのよい果樹園で白桃を育てています。
34|広島市|ひろしまし|広島湾|ひろしまわん|湾|34.30,132.40|かきの養殖|かきのようしょく|島が多く湾の波が比較的おだやか|いかだからかきをつるして育てる|広島湾では、おだやかな海を生かし、いかだからかきをつるして育てます。
35|山口市|やまぐちし|関門海峡|かんもんかいきょう|海峡|33.96,130.96|ふぐの加工・流通|ふぐのかこう・りゅうつう|本州と九州の間の海峡に港町がある|港町の市場で集め、加工して各地へ運ぶ|関門海峡に面した下関では、各地のふぐを市場に集め、加工して出荷します。
36|徳島市|とくしまし|吉野川|よしのがわ|川|34.10,134.54|なると金時の栽培|なるときんときのさいばい|吉野川の河口に近い海岸に砂地がある|水はけのよい砂の畑でいもを育てる|鳴門などでは、海岸に近い水はけのよい砂地の畑で、さつまいものなると金時を育てます。
37|高松市|たかまつし|讃岐平野|さぬきへいや|平野|34.22,133.94|米づくりとため池|こめづくりとためいけ|瀬戸内側で雨が比較的少ない|ため池などに水をため、田に送る|雨が比較的少ない讃岐平野では、ため池などで水を確保して、米を育てる田に送ります。
38|松山市|まつやまし|宇和海|うわかい|海|33.25,132.47|真珠の養殖|しんじゅのようしょく|海岸が入り組み、波のおだやかな入江がある|入江で貝をつるして育てる|宇和海では、波が比較的おだやかな入江を使って貝を育て、真珠を作ります。
39|高知市|こうちし|高知平野|こうちへいや|平野|33.55,133.66|なすの施設栽培|なすのしせつさいばい|太平洋沿いで冬も比較的あたたかい|ビニールハウスで作物を育てる|高知平野などでは、冬も比較的あたたかい気候とハウスを利用し、なすなどを育てます。
40|福岡市|ふくおかし|筑後平野|ちくごへいや|平野|33.24,130.55|いちご栽培|いちごさいばい|筑後川のまわりに農地が広がる|ビニールハウスでいちごを育てる|筑後平野では、平地の農地にハウスを設け、温度などを調整していちごを育てます。
41|佐賀市|さがし|有明海|ありあけかい|海|33.14,130.33|のりの養殖|のりのようしょく|潮が満ちた時と引いた時の水位差が大きい|浅い海の支柱に網を張ってのりを育てる|有明海では潮の満ち引きの差を利用し、支柱に張った網が水についたり空気に出たりするようにしてのりを育てます。
42|長崎市|ながさきし|九十九島|くじゅうくしま|島|33.17,129.65|かきの養殖|かきのようしょく|島や入り組んだ海岸に囲まれた海がある|おだやかな海でかきを育てる|九十九島には島や入り組んだ海岸に囲まれた場所があり、その海を生かしてかきを育てます。
43|熊本市|くまもとし|阿蘇山|あそさん|山|32.89,131.08|あか牛の放牧|あかうしのほうぼく|阿蘇の山のまわりに草原が広がる|草原に牛を放し、草を食べさせる|阿蘇では草原を利用して牛を放牧します。人は草刈りなどを行い、草原を保ってきました。
44|大分市|おおいたし|国東半島|くにさきはんとう|半島|33.57,131.59|原木しいたけ|げんぼくしいたけ|半島にクヌギなどの林がある|クヌギの木を原木にしてしいたけを育てる|国東半島の周辺では、林のクヌギを原木として使い、しいたけを育てます。
45|宮崎市|みやざきし|宮崎平野|みやざきへいや|平野|32.01,131.41|きゅうりの施設栽培|きゅうりのしせつさいばい|太平洋沿いで冬も比較的あたたかい|ハウスで温度などを管理して育てる|宮崎平野などでは冬も比較的あたたかい気候を生かし、ハウスできゅうりを育てます。
46|鹿児島市|かごしまし|薩摩半島|さつまはんとう|半島|31.33,130.43|さつまいも栽培|さつまいもさいばい|火山の噴出物が積もった、水はけのよい土地がある|水はけのよい畑でいもを育てる|薩摩半島などでは、水はけのよい土地を畑として使い、さつまいもを育てています。
47|那覇市|なはし|沖縄本島|おきなわほんとう|島|26.47,127.90|さとうきび栽培|さとうきびさいばい|一年を通してあたたかい|畑で茎を育て、しぼった汁から砂糖を作る|沖縄本島などでは、あたたかい気候を生かしてさとうきびを育て、茎の汁から砂糖を作ります。
"""

CAPITAL_DATA = """
01|43.064359,141.347449
02|40.824294,140.740054
03|39.70353,141.152667
04|38.268737,140.872183
05|39.718175,140.103356
06|38.240127,140.362533
07|37.750146,140.466754
08|36.341817,140.446796
09|36.56575,139.883526
10|36.391205,139.060917
11|35.857771,139.647804
12|35.604563,140.123179
13|35.689185,139.691648
14|35.447505,139.642347
15|37.901699,139.022728
16|36.695274,137.211302
17|36.594729,136.62555
18|36.06522,136.221641
19|35.665102,138.568985
20|36.651282,138.180972
21|35.39116,136.722204
22|34.976987,138.383057
23|35.180247,136.906698
24|34.730547,136.50861
25|35.004532,135.868588
26|35.0209962,135.7531135
27|34.686492,135.518992
28|34.69128,135.183087
29|34.685296,135.832745
30|34.224806,135.16795
31|35.503463,134.238258
32|35.472248,133.05083
33|34.66132,133.934414
34|34.396033,132.459595
35|34.185648,131.470755
36|34.065732,134.559293
37|34.34014,134.04297
38|33.841649,132.76585
39|33.55969,133.530887
40|33.606767,130.418228
41|33.249367,130.298822
42|32.744542,129.873037
43|32.790385,130.742345
44|33.2382,131.612674
45|31.91109,131.423855
46|31.560219,130.557906
47|26.211538,127.681115
"""

PREVIOUS_VERSION = "geography-prefecture-discovery-2"
ARCHIVE_VERSION = "geography-prefecture-discovery-3"
DESCRIPTIVE_VERSION = "geography-prefecture-discovery-4"
TWO_QUESTION_VERSION = "geography-prefecture-discovery-5"
VERSION = "geography-prefecture-discovery-6"
CATALOG_REVISION = f"{VERSION}:prefecture-prompts"
# 年齢の帯は、ホームの年齢設定と単独利用の年齢選択で共通。
AGE_BANDS = [(1, 6, 2), (7, 7, 4), (8, 9, 6), (10, 10, 8), (11, 100, 10)]
SKILLS = {
    "map": "位置と地形",
    "capital": "都道府県名と都道府県庁所在地",
    "industry": "特産品と産業",
    "reasoning": "位置・気候・土地利用と産業のつながり",
}
PREFECTURE_INFO = {}
for row in PREFECTURE_DATA.strip().splitlines():
    pid, capital, capital_reading, land, land_reading, kind, location, industry, reading, climate, use, link = row.split("|")
    PREFECTURE_INFO[pid] = dict(
        capital=capital, capital_reading=capital_reading, land=land, land_reading=land_reading,
        kind=kind, place=location, industry=industry, industry_reading=reading, climate=climate,
        use=use, link=link, name=PREFECTURES[pid]["name"], reading=PREFECTURES[pid]["reading"],
    )
CAPITAL_POINTS = dict(line.split("|", 1) for line in CAPITAL_DATA.strip().splitlines())


def project(pid, location):
    lat, lon = map(float, location.split(","))
    if pid == "47":
        return [round(523+(lon-122.75)*22, 2), round(444+(27.98-lat)*26, 2)]
    return [round(44+(lon-128.05)*28, 2), round(29+(45.68-lat)*32.5, 2)]


def region_of(pid):
    return next((code, name) for code, name, lo, hi in REGIONS
                if code != "all" and lo <= int(pid) <= hi)


REGION_READINGS = {code: name for code, name, _, _ in REGIONS if code != "all"}
MENUS = {
    f"geography.discovery.{code}.{count}": {
        "menu_id": f"geography.discovery.{code}.{count}", "category_id": f"{code}_{count}",
        "label": f"{'全国' if code == 'all' else name}の都道府県を1つ発見",
        "category_label": "都道府県の発見", "region": code, "region_label": "ぜんこくから" if code == "all" else name,
        "difficulty_id": f"discovery_{count}", "difficulty_order": 1,
        "progression_group_id": f"geography.discovery.{code}", "skill_ids": [f"geography.discovery.{key}" for key in SKILLS],
        "prefectures": [f"{i:02}" for i in range(lo, hi+1)],
        "mode_options": ["challenge"], "assessment_method": "automatic",
        "estimated_duration_ms": 100_000+count*30_000, "duration_basis": "provisional",
        "question_count_default": count, "planned_question_count": count, "age_min": min_age, "age_max": max_age,
        "supports_direct_launch": True, "is_active": True, "next_menu_ids": [],
        "selection_instructions": ["都道府県のピースを地図にはめる", "拡大地図で地形と産業を発見する", "特徴について答える"],
    }
    for code, name, lo, hi in REGIONS
    for min_age, max_age, count in AGE_BANDS
}


PREVIOUS_MENUS = MENUS
TWO_QUESTION_MENUS = {key: {**menu, "age_min": 1, "age_max": 100}
                      for key, menu in PREVIOUS_MENUS.items() if menu["planned_question_count"] == 2}
QUIZ_SKILLS = ("capital", "map", "industry")
QUIZ_QUESTION_COUNT = len(QUIZ_SKILLS)
MENUS = {}
# Keep course identifiers stable so the planner can replace the published version.
for menu_id, previous in TWO_QUESTION_MENUS.items():
    count = QUIZ_QUESTION_COUNT
    MENUS[menu_id] = {
        **previous,
        "difficulty_id": f"discovery_{count}", "question_count_default": count,
        "planned_question_count": count, "estimated_duration_ms": 100_000 + count * 30_000,
        "skill_ids": [f"geography.discovery.{skill}" for skill in QUIZ_SKILLS],
        "selection_instructions": [
            "都道府県のピースを地図にはめる",
            "拡大地図で県庁所在地・地形・産業を発見する",
            "県庁所在地、地形、産業・特産品から各1問に答える",
        ],
    }


def previous_discovery_questions(pid):
    info = PREFECTURE_INFO[pid]
    region, region_label = region_of(pid)
    same_region = [p for p in PREFECTURE_INFO if p != pid and region_of(p)[0] == region]
    others = same_region + [p for p in PREFECTURE_INFO if p != pid and p not in same_region]

    def alternative(field):
        correct = info[field]
        return list(dict.fromkeys(PREFECTURE_INFO[p][field] for p in others
                                  if PREFECTURE_INFO[p][field] != correct))[:2]

    def q(code, prompt, answer, distractors, explanation, skill, *, reasoning=False):
        return dict(id=f"geography.discovery.{pid}.{code}", prompt=prompt, explanation=explanation,
                    options=[answer, *distractors], correct="0", skill=skill, reasoning=reasoning)

    def choices(field):
        return [x for x in alternative(field) if x != info[field]]

    kinds = [kind for kind in ("山", "川", "平野", "湖", "台地", "湾") if kind != info["kind"]][:2]
    if pid == "01":
        why = q("why", "なぜ、地図で学んだ地域では酪農がさかんなの？",
                "夏もすずしく、広い牧草地で牛のえさを育てられるから",
                ["夏の暑さをいかして、暖かい温室で牛を育てるから",
                 "海に囲まれていて、海の水を牧草にまけるから"],
                info["link"], "reasoning", reasoning=True)
    else:
        why = q("why", "地図で見た産業と、土地のようすはどうつながっている？",
                info["link"],
                ["土地や水のようすに関係なく、どの場所でも同じ方法で行う。",
                 "土地の使い方より、県庁がある場所だけで決まる。"],
                info["link"], "reasoning", reasoning=True)
    if info["kind"] in {"湾", "海", "海峡", "湖", "海岸"}:
        wrong_site, wrong_use = "雪の多い山の上", "山の林で木を切り出す"
    else:
        wrong_site, wrong_use = "陸地から遠く離れた深い海", "船で沖へ出て魚をとる"
    return [
        q("land", "地図で発見した地形の名前は？", f"{info['land']}（{info['land_reading']}）",
          [f"{name}（{next(x['land_reading'] for x in PREFECTURE_INFO.values() if x['land']==name)}）" for name in choices("land")],
          f"地図で見つけたのは{info['land']}です。", "map"),
        why,
        q("capital", "都道府県庁があるのはどこ？", f"{info['capital']}（{info['capital_reading']}）",
          [f"{name}（{next(x['capital_reading'] for x in PREFECTURE_INFO.values() if x['capital']==name)}）" for name in choices("capital")],
          f"{info['name']}の都道府県庁は{info['capital']}にあります。", "capital"),
        q("industry", "地図で発見した産業や特産品は？", f"{info['industry']}（{info['industry_reading']}）",
          [f"{name}（{next(x['industry_reading'] for x in PREFECTURE_INFO.values() if x['industry']==name)}）" for name in choices("industry")],
          info["link"], "industry"),
        q("kind", "地図でたしかめたのは、どんな地形？", info["kind"], kinds,
          f"{info['land']}は{info['kind']}です。", "map"),
        q("chain", "地図で見た産業につながる順番は？ 気候・土地のようすから考えよう。",
          f"{info['climate']} → {info['use']} → {info['industry']}",
          [f"{info['climate']} → {wrong_use} → {info['industry']}",
           f"{wrong_site} → {info['use']} → {info['industry']}"],
          info["link"], "reasoning", reasoning=True),
        q("region", "このピースをはめたのは日本のどの地方？", region_label,
          [label for code, label in REGION_READINGS.items() if code != region][:2],
          f"{info['name']}は「{region_label}」のコースで出会えます。", "map"),
        q("use", "この地域では、土地や水をどう使っている？", info["use"], choices("use"),
          info["link"], "reasoning"),
        q("name", "探検した都道府県の名前は？", f"{info['name']}（{info['reading']}）",
          [f"{name}（{next(x['reading'] for x in PREFECTURE_INFO.values() if x['name']==name)}）" for name in choices("name")],
          f"探検したのは{info['name']}です。", "capital"),
        q("evidence", "別の場所でも、この産業が広がる理由を調べるなら？",
          "場所を地図で見て、気候や土地・水の使い方を比べる",
          ["地名の字数だけを数える", "県庁までの道の本数だけを調べる"],
          "産業と地形・気候・土地の使い方を比べると、場所によって成り立つ理由を考えられます。", "reasoning", reasoning=True),
    ]


VERIFIED_MAP_DATA = (
    "eNp8veuurkd1Lngv/m1Zb52rcg1VN5CtqBXtjXZQq5NWOt1/okisBQQfMMbggAET42AbjDHYOARz9MVMz7W8fuUW+q1xfL75"
    "rWnJWhqzXF+9o8a5Ro2q+udnjvDMX/3zM//3P/7D//p//+c/ffkf/v7/+Nt//NLfPvNXz6wSx3PHs+Goz7VZYn1unHB5Lp9w"
    "ea4B3KlPPeFMfdpzgeB6wv2544QTwY36xOcCtZcTPp7LBMdZwngunfDYvw1N+py/DfW5aH0K4dOoPRB8fv2ED/pt2e3nCHvM"
    "vHHeo51w2t/aXzzhKPDGJzw3CB4EV+rP7Y3G3/3Pkak9PTs6gfWc7mgC1mcHTfxEKW4wOXgQePYt9sXByJ7DPzvS/llIu0Pa"
    "PzunH6XDSRUCE4E0QiYw7XE3GBiHTtQcGyxE8GN3YNoHwewE2+5wENj3LA5iWnl2DAIr0ZFoESvxMhG/B82/0tAmB399CkXb"
    "n6z09b5xImKcYN7g/mXbnySGRSIRg41pyK1F8e8baQXDBgP1rRvknw1vtQ8LkSsNljfI6LcNFpnVUMGN2lqwbxCOMTGqfCJo"
    "X/3aXz/zLCrH//zyP335S//PM3/1P565ff6dR7/93ePX/nB2+OyTDx79/AeP/vOd/effnD/40t/+n7vTPz/z93/7f33pVKbb"
    "t3/25Ee/uP3oo//+0/M3X/3mzcNPb776/ZuH7988fPfm4e9uvvrD//7TC//9pzceff+D2998/N9/+vdzzFML/9eX//5/nz++"
    "efDmzYOv3Tz40c2Dt28efO/m4Xf3KA9+Se2/u3nw0s2Df7158P2bB3/gUW4ePLx58G83D35z8+AnNw9e5eH+7ktf/t9/90/P"
    "/FWMI5wI/sOX//7843/kcurFSZ/8XEl/8y/PGr6PPnrz8xd+feJyB5Hnbx6+wKPCkC3BiKmeQnuKUb075O3z791++EcmgcC/"
    "/ubtT98/cb78yMMX92T2vzpVb/ntzYPX+Qf68dAizufUqdSfzaf6/M2/nIz4xy//f1/6xwtOPH7z48cvvXf7ux9vvv7tP/3d"
    "tnQ5b83vWzJy3pLct6DmvGX2BMfKJCTbxJw9xMxtMdntbKrOPnlLex+7OW/rN05CnL+M24CFuAc8lfjsfVqAvHJKW+zyqdA5"
    "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"
    "CXO9EH/rEu722yQ1xoXgJltVG05Scyu/pdWmjE8E2vAhK1iFtwJo/yo4BHkAZOOpK4cNay0Z0eSv1Q3w7e+c3uYbzRtJAd+S"
    "3ojDAtMSmV9pacRhunxa+w83QwZngru6MSYowRuJLuHLRi6KKU9HMHPscCa4EszM2OMf8q0GMIcyVZnKZp1fdRGYJJrGjPzy"
    "AI0Z+dZ8Nv2jSOjA9EkaJvILA5z+51dUnIb37gM+fveV24//i/cBP/vTi08evMbwo7deffTi649f+8PeH/zRnz9/9yWGn/zk"
    "+c8//oo8DrJ/8sNH//nO479868k3vrk7PG0D8fFPv/3oP359vdn3Ie21/cQ24HAnsQfcbtsJmk2EU3Uuiv4ff+NnN1/9Lzq2"
    "/sajN//z9lcv3P72u9ebfb+hnb63aNfyTTq5Tjt9G4Gv0X2r3755+MKd/b5UEIF9oOrk+L5X8eIww+1Hv7/9+rduP3rKDbIv"
    "0w7pz+kTd2bXW8ETDaeQbWk6PVC57wTC658++uDdJz98/rrybcubptw6wVGWs0mqQSic7bp3zCmKpvvFPXlh4she+EjPl8uh"
    "lN6kgLUTbEXJnYutk1j6aB51SFp0G5EmFj0SHGS5maxaIBCenHZNiv/eSOF5SZqT+kz4rRa59mov72zPOaToPFmVVGIcdPtu"
    "aHqMdT/IcjxxZZ0YoGpVT/u3UdJLiv9wfIhuQmdKGYqBI29Ahs9oW6VIN5L+ZtlOSVJl1wTPsAA3rXoaXcavNOaY/q281Pg2"
    "WXYPGrNKWigd+nqJ0MT4FcSrszduUtW2pbBN/Va2yiuSTq0w7EM8fKaowQpM+YUmrmcYUSp8BNaKoxGk4FvGnDAvvWiAX63h"
    "g0w9+oUCvG0uUUySVEFS+2yOsGnl2Mh+CIdfOOED/72LzDAc9AKIEbwGYwRJVWaTvaR8ly07d8YiV8ZrqDkZXLBrY06nv74k"
    "s2XYKjZ7BV5E2cIaBJvMyzjR6SlyGOwFGHKoNt8iQUAnOOgBgKGHlwrBZcFvRUc2nBbYkwn6ssBWTJCBBXphulC8QFxeVaOU"
    "3vAtMqdzVh0UGhahs/B0gSxpBdQIfqBoNAlc5Fs2X9fZyC/AWFSbIdoNC+AJ9g3olqfDYYFeT8B5Ac2N/ow/VUDxi0wSrUex"
    "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"
    "1edpHnFMupf2hbBoj/B+sXPOmCe+PfaS76G0n5YX9KHqE+WNvEjXPek9tPlYcT3k6Laf75yUPvnWr/78zi8ezNNiFbluZCsZ"
    "7y5d2s0q81VLHHD1k3h7O7s5og5LypqybRe9lZDYgELV1IqduG5oLQkZN5P0d6sWVgoK0d7IU9qp3FkaKnVFb0tlL6gbmbNO"
    "z056sVRx06QgOL+YmtOECMr6rcJc0CpWc9MYY0cJeE4l4vbhgj/am5PAGe1UWaqtUfCcrKql/1bXVS2VerGU5nMTDAJPtHlq"
    "PNUca0AgdLXtB+OtfVtX0TczYbtST9UxVcf6XqXbv55yAadsSyWBB7qwr2V8vGCwwOlD97kI/5t4wNWQqnuHWeCvdguj6knf"
    "3qq9t7VtPKB8kg8+DwwCT3U6RtC6LcLVPjiMJpbgjQG6JDcvlF4dNyCXXFhF0u5mdMMxI9E8DuehxbYjWTvbj/L5gYHgqZtw"
    "tcw0Fz6pCXgrprYc/+nhfVG+WxrgKYt4cpPMivxmm6cmwpvT2sw4nefwzCYaLZIvWldd9Nt9eLsRn2fhz2iFmA+v2jbTbPuM"
    "yLJsJq8dg5vhv1CVxzOn9CeXx3LoW61SXV/nW1X4M9tt79F722RHth/gNoI/O83vt8Clnffg0kD3Lv2T+rvdspUO3RKWtRu2"
    "t2b91d+ebft8wEPY9C2ie3MzpeF4X1zfDk/4crWj6YFqWZDzom/J+Ga3Y+e323SF6rd0bi0PbgnPfqyFvCfSq65zFu1N++wR"
    "qpe6y5HrukU03SSbdh0APun4bRE8H/4sNL/TVPS835aW5NWdSbc73yr+K+l/n9OOW67fhq/3JNS48DlsPz17jZk1TpdM+io5"
    "HfuR09LPa8HZH4UfrDQJ7TUkj4rnQPo/+XrnqQ57YDZz3Pkz0f7orwK+3ymevQppoSqkpQBmxVty/NueFRbJ4Ka9Q+S0uJle"
    "z+2tmqHY1wZgjotkbZNusWMk+Mf3XLu2Ax1d9y7SmZvspUU2zCack61SaV2R9uVAdkVfhEOBv5PcNV+X20iLbK1NtFgka5vs"
    "okU6YROPLdI5m3iS+FP1RiR4AuF5kD7p3m82UlkkU8K3g/ZZ3wePblykS2k/DYv2Atrv2qK9j+zGvMiGdD0vIclH52/SFYt0"
    "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"
    "CYebaEp4DoS3sk47Sv9EJIp9dwB+24YvOgZsP7QWGY8yWZt4XubPiIoinhE4OyJvrjHVv1sglkp3y9B8tZPR6+BqES0EP4nk"
    "CLjaxJNOxy7yqFEFQejov90E2yLcbpLBRby0iWcWycimtS9ao+Pf+qf3B3jxz0WwbVr7IlnYxGPCbxVRU7TGRbTbxEtE97pJ"
    "phbBsGnORTptk65bpKNIb8xFOoTkqJI+yZt4ZhHPb+K9RbplE28swuEm3n7QJyTvd/Ry3UJ6Jj/oK2//BR8YbpsGgs0QIZHT"
    "CxcCUSsmSvmL2AcSJzVpTyS8i1qJSSW920H+9vXePWnUaV9jmicZjCi+J1RGUb7rqipqhSAxIq09ZUyFRCRpZ+Qmj1rtVamP"
    "Sk/anxAvmaTtmg1F+US6uyUDzTImOZzZDcqolVmlSGDUKoxXkR8fL1ykVXub7HRa5FCM+6gVrB7aRWCu3l/xW13jtB0QBQZF"
    "urX4+eUUZfgU4wl0kYNZHBHt7G3htCHwy2H/tC/OF+m+fJmlf0r7+m1Ff5IxE8UerV9oOvTQ1dGuPr7hwiFLu+HyARrG2xEX"
    "ERc/BofB2knaOqZJu6L4pPCvj5n0rQH4m2la7Z8RRSybScrl+y/tYfhUDSmXNoBBaapaVIocXniwZLLAlcoC2lnWldAe0u4m"
    "O0MvmrQ/4FCXpO27W592PSHtbHMeGXzZq+gHf3j9qx+qV9GrL3706fsfvFgU8bfvfPLNX8O751u/oT8fr1m+LfcqvyMHn3ef"
    "Ou8uW2JqpGW0/u+Vdfo+FPcnP3390ede/eKj5/sOvdf5g3zhe085PVoYfJVzo+kNiVdY6329lq++9ck//1xvjh6m/2fJ7PFt"
    "vypi96TBc1/X9ppVJteXslh95+tXdcl7Sxo0U0s3mpxv4xuR1ZGxSwVpu9XlOjS6fryMfdOPBf0VF6k25krWc8lkNJ14vmU7"
    "xOV0KTytB5cpcDbS1245HZiddwX+PnDRefhSdsrRvRbGJefDLP5uF8F50W/lu90sGPD6dfC95rH4aJpzXzBE1IKJWp1e9fgw"
    "a+lae/BaM1cbtWPkW8N2/WH55/s+7bZsjOzKY0JfZ9EdegLpm77lMAzg0HJenHUpzieKzF5zKq4Utx2XN1e7GjzdklUXn6eK"
    "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"
    "bjfx6iIZ30SjRWvfJIPCD9nHe3sRz5Ae6KTrBunPQXSZm2i9SLcQfjLxv663ET9bVWaSzUU43KTTFukE0huD+HA+4f/Mc79e"
    "xkOnfuxfbONfFbZA3vuQwO/98fXPHrfAojeechQqdjvcpN9v/4u+Qsmxt1TzW7iN0VrqYn2WiNvza0nJS6nFklD27KYasi5b"
    "LPU8cIM85FvVbKJS8e5/qeyM5+1LhDLUR5X+KWO69HeU7KL2ot/e+gssyEtUCmyrIt9t9hJw1nuDU5/VBZ48YKP1TTAT/JfK"
    "brDdosyj9t01f0D7gjNgjUPmn2bR5gnLOAje/MR1cCtwFvMVAcySsuLAJvPob6vAo/4kXWha1F9C5s9mbZdkNuYm2i2CeRPt"
    "nI6S6uCs/fZde/WZ23gjAZ/6MpHpu2MRDDK+m8/M4cNNayH8Z+cTYX2n3diEW4E/Ox+Gs66D801rF3ii0eXwnvDJMPwcGBbx"
    "8CbaLeKZTb9dxHubaLGIZ5wPG+Sr0TzJzhDFfHuawD/NjeXI2j44L4twtem3i2RnE02JLuOBn+/hHEYX0K5BVww7x5wxIo+B"
    "4ATMm2i0iEYEfyb+KYSfuUhXbNIJi761iSeFP4fzp+u3RTKyaS2Ef8VPdL5y2XTdmECvZC9S3p6LZOEv7nMnJlWfVwS43L+0"
    "F4vN6Plf/ABxbhffZrS12ExGkcKrXU7BwtSwkRRp6yY3b20rjDqkf1pZe9xxSFxDGm7wXe3m7e6Gpo2RCJfU/HCSkhq14luI"
    "O4IM2LCWv9wpmTNQ9A8oQPbhJh9LVksaQEcAFHzBPo9OOqz8Jf6HrdhuKqwdaDW38Z9RiuU/Pv3O5148Y7/z4+ez6k8kEcB7"
    "z6frWSs7Rt4O+EUPq3elTj75/jvPc374dJxO865syk1r6SXWfYaqT9//4M9/+OiNqUT/WrxyPnohlehMnUNrbkQrWnKsvXSw"
    "/vl7r77z4OqScGUlITRgTcn+kSoqm2ttC60EFaS2hV2nXTVz9OrrqicScd1VhfUztRWsiNoZqE4mdRlQLUpqRqC6VJynPwVU"
    "WdQaJf2pXQi2Qv1ha60nVAxL8VQdjFbVrct4rQDZ9iWiwYqIJys0XjbBL2sZtBavmujrqjJPscpvEPuOOg7B1zhQhXJuGiP4"
    "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"
    "dHVrV2GZklv0/by6ODldkxJpcIZ1Ca6dnbRWHaHWv3h/c2AmPFEP6yvPWm+42mqD9uLPXZ9wcljw7Gbdm1mUbJbMnfNq4fKB"
    "FbKZ87k1OJ/1aXB3nCo9lRfyTDjG7wd4UfBsNpyuzbxeA0+nY7VRfunc+wGLNZbxVDcb5sAfThOx9L3ulR+8i6hlU8wJ39TZ"
    "3rxO1gnrc93RVwbDM0zCH7Vszv59Ej7rpKfSuQlt4dxeJIckJ8ck+REaBnNKO93SJJpc+qTttO9pO9J7gpM8L5I91F2SCwLB"
    "rbg8GJ557vYq8h8Mt15o7pX0KOByKgieuEST3+pqeUj/YoeOLZMuqwHj+85o95ffZlvNurlQk3yrGz17gmzr0/Vwxbod0A22"
    "WihZtXrZFwFbLwxnXc323Jc+J4+NtMNlET0n6cIimyD9i+3soF+SVNmzXVhIfz0oddNH3TDr3HWXAVh3MW4rZF7NVmmnf5+g"
    "VU6Y72EHMf+W4jnsQgG2LkKnml2cQUfEcaf4qyMCY8pBb/OObI7qzmEXjtveLuCcD+gU7MyCfdNLyd1nbX3vk/RR8NGLnkEy"
    "rLXGhl1QbhkQ+fFLoh7t8mgRDd2uih3evCC+x0Wy53IoDoQtqybzcJC6PZlkK1yuGmw1ZGCRHZ4kMySHxeQ2ShLmpjnRX/Ul"
    "0XyhOyI/jfhymD0HrPpI/MLa1zGvwx2YrlNCtypwWmSHJ8mSradRkrS3fVjbtrRJuunrYPZaWgIvsqWTbKDri+qdr90LOgj8"
    "y3bAbt2ctIaafQCePvdFOjVB22z6WH2N9vX9ATz3viLDzujpqi7SwUm6v0iWJs1xka2bJNuLdHOS7i+a+6Q5LpKlSbRyfBLs"
    "8D4NOK8n6ewi2ZjEa5f/QfIvjqO91syty43sT52ky4v2ZpPWnUW2lNavSHrhfE8BfKm0LsOGrG3r9r5xYL5+Ib5lkviYJ/GU"
    "7NWgvUonO59J3wutO2kSzU2uVE+3zi5a3yetfTR+mWRbaB1PhGe+sc/Q/UUySet+oz3VMWl/Rd9NNK98I5++Lm/bO8lGLdof"
    "Ttr/3NgT3+NtWz1pz7xorSS5TffWHV5fXDZoXteOqQsdseSWe6+9nVGz96LoDuQO6DE2W84LYI0JPhAPr28JRoufl3eJNX8h"
    "jOa5VyessfRNYI35P9+z1d8Ky4cs/0GW9pE95ysMy9M532eOnusRRto5a4fBxSLDNWZ+4yk4W67HWem+67cu4xyGgxzhi+Os"
    "x2TZEg3LIzjxyZhvwbuFyDE58s5NOKL1wXt9RpMKPM+jdMW8Tjp00LnLsV3pc+IjkXlB3/vVfCgRzVE9h+WEB3hx0qpQ+2Hz"
    "xfFftj57jjJORq4BjSnztby8E970zDt/8LDcnNMESIyL4t87eN2Fv92/G5FzFGW+h7d34NZlHO2T5x5T3ynFtxB1L3kWwsds"
    "8tMHaJUW4SDjKK/Dot/6OAnvUnoOyJZnkbcImSfZk/YDuSHUZ5GsTuLFIhwEz4PkPJJcZcjVlu0wiRfLdETlxGm7SO8myR7e"
    "w9x6cfj4roOTeCH0DCZvXWVG9SIC5zj33IeMA55O0vdFc5w05iJdE73LaCednaRTi2R70rdI3irJicpbIH1hvY4+X9eFRTSf"
    "ZHMW3GveH79dpMuTaLtI9ibZFpKTMYl3i3R80rcW6QjR+VjEi0kyv4iGk2zFIts1tz1Pi2zsJJ7ejJN9HLN7eZINXGS7JtmQ"
    "Rbo8yabRmsL4xEW2hcbPV1G5l22aqnJQ/2s+HvK/Bl3rpS6U5tqrZzp0tF8mrXnfugfQpEBdNzWXX4PWNFFM941aClTX6Bix"
    "r/ByoclKhHrwZIwIntRxqgV9aRKqBlVq8rQGNwYLnrwwPFBwY7DgySBwsPOXJszpt0KGz6cJHOwsr0lveq4Mae9hNJnMYQ9E"
    "1AQ+3c+EsMO/QkB7FriY7yKEvW9E/4Qxm3n9NZFOz+aaCKs0DAV7m7MP7c837x72K3/3D3e//VxDwp7+8V/Ph24e8DE/++Gf"
    "7r763a0z+LPHr/7kttDIRVmuS20WXK1e1QZ58pdP7v761U1VkNMLfAaPsWv54Div08GOcJJr3/IbHz///M+asPT0e29oztAL"
    "s5U+fvzqf53f2QlLPxKn9s4Zus5ZKp1Lh54CoB7o9lAxEhDz2gl9WPToheFH34cSFViNGtAMf42Kigdu77splkZzhIr+Q5ic"
    "7Opl9xGF8OgPrQigzjPNelXnWbDozuyCLMX7gt3qqzI1/25Gn+KKIoe8YM65Mjdul/GPsSNefe4nnnHjHy2api76lnzXoxJC"
    "xsE9i+B3O5SHY0fIypuAEoUq3812eHIcmrR3i7Q9xr6ig+IeUFydl9Knm+NcMzl9vs355XMXY+nRcJotDHr2HZWzeS18yc6X"
    "sKPD9m8n0XxtmWkkP2MRryfxTvpXc8Y7fOLZICeK/yB8qkWBqfHGvBLRx2VmbZpXob9ef7ZFY8r4HuW3ZYDkIS6S4Uk0XKQL"
    "13qxZYzk7aRDgLPkmBsO9+TH4UW6MEnXbr4bnD4RfAlzw4fI1SC5gozd0HPLecDVe5wEEz0LybP2T3Zt73C5kc+tF66bpKe8"
    "AxDpUfK3+/mOz799Lx3R1vQC8W3mWwvm8xyC1qFrsaNVsGZ1N3MZd1WN19Bla5bc6QSLbkiLxhRy6LrfFsHSrncraZnq2jrb"
    "TT20ppO277ksmovMq5jPLfQdJx7avn8JeUcc7LmIuGTHv2E/o+MX85nsMQWfYSHgG7dl67jR4fDvtn2HGCxpQs16F5XOvteq"
    "aM+2z1Gzovc7L9yrZDPf2HvU7cvafSbRdtEcTb3Rv27f7Obpoj6TviV4+l3Jpsmy/V6l/aFs5KMlArRJfRbNfdLcpd33b/tb"
    "i2gyqc+63telfZe0ZXISjxbxaJJsyPiD+NIN/3vys/v7HCf99gYfwKzGp+HX7WREJEUOD+3kNdldb3WPjNmdC0ncKUgalaDp"
    "FceBBaNJezAKo12wOgJtaOL21B1xe0cdPtsTtO8QOJnH+0g7pUgLD+hN3FFoTIuROaTdb8GOglNGFNhTV9S9oR5yyeGH4T4i"
    "FrbucAdu2W5e9FivXlPFU0OODwsRVBpGC73WogIa3nxUau8IBTzHFC1WT+9R4V0/BE52g3PUfctw1B0ifrQdy3O0vWmQ4gfY"
    "eGkCqS9CfmugicF6Iri3IfOIiKMTX/q+Bd6bBsMHm4m6b9kOS/VS2LNqtrw9XI3gq3fOklt6+vjgq6ePPn8oIeXuN/95e/T4"
    "3Qtf9TyuXvV0zh/XGSG/+fmzH3x699nn94Z8JM+F3jt8jFGvDx8BuZRXIz56QYXDt27Qy0dm/b3onsZ9t/BQgYD3f/D0lY/v"
    "HyQsHi07zRP0pdiNw9Hg7Q/GL73xOehE77qT1ot0Sm4cVO90M6T6qIcBLUagmw+Ved3E7DFZT6Xd4xP9t2Xt32p/4LYwL72h"
    "Puzm4limL6ZHh90sqL7rJnjjLHSoFoqsxQv0hlqLgmjKxh5zbT09Jv3W5qU3Ghs3p4/aigw6D2/vsEWeAoBxJALhsKgA5Uty"
    "/K1PWjSmjDMsxHfDk7619rfUZha7UVWbD/wd50U0mSQzJieYV6H+ZYdGb54Sv8okWi2SvUk0p3Gy288B+kTieyC5DdR+EJ6e"
    "ErLnuEg2Js2F5OSYJDMkz4XkU/GpJP9brlwXJvFuEU+p/yC+VJKHdsPfLT8uA0SfRHRjfDLhWUl+2tWmv0jg3Gn+r2+svvvH"
    "Z7//8X0TE/em8GoJj1iqTxV6eDlvtpk+LKGy85KwwmFBEuVm62CXkcMSnNMcDYtPXeoO1daObUyX8faWI5gZFLhiozXML1jn"
    "HmRplKjeOKsbVXd9x0H7pWNHGvhepUya3NoYzv0dGaXZnv4I2C/GRdOcROqlfnRBRiNZNerqap/lhFu7y9yzWDQLwnysYXnP"
    "be7PnHgfOCxsessYfiY7jn3m2Ozn3RxRK0/67docmvvzi0b0/aQ4hg674VVqJf+qM5H3nIv6TBKARWNO4sAiwRTsPWZ8w7QX"
    "vXrN4OQRMsJRMjvHB3baerckSA3zaF+IWzb1M84o5QQD6gvo9ZTcaGMEaY1edGBEDylEa9UOwdTBdu9lg9Kasacfto1vBp5W"
    "cxwYTFrtRDYOHI7b1Asm2e0NZVzTDnGPUOBA7wNgPMEIfPXqSnDw1nCCVggB4DmhPrzcAT5xTsg7ZAOLDpahAN1EeszePb6x"
    "Wz2AZjicvOiWud+sb9ZxBwLyu6XhZ+tw+pR6h4srnuCBzXbv2CtVA7OCEaaxNw9lws9OuezNRa6b/yBb67mZ6829EL15ugXi"
    "fs4dvIdthIloDrQ6OtUzBjyERMAGp13XbbxMqOJuQT7RbfINpQYch3Pb2JsXEcCEgk7Tcld696UUNDuUxwl9x8FgQ0COXgbL"
    "10bycI2tTi+vERDpkU9R1Yz/YlLbVMIb6m9A7kU+9VDd9Gcd8b0j4qrn2K2ChB3GR4RfoZju1a2RAM0Rda2nx9besDHTDnGD"
    "xT5xHvLws3M/gZ+NrchDFbkjBBNzGzo3kOTlhYoI5xYeRRBOV6Lm/ck1XIu+N0ffk+6a/CWFIzTfSzbjyPs4nZSeDhUmZUx5"
    "wkudmtIl4rVxeHkhaEiUtuAkeZHQ7GYKkX1VBRB9v+m4+PUX7339z18+WLDuF599/fcPpFTBh08++OTZ579+YdkCrTv/ofyr"
    "RQo+lDp1P6aWq7IFqfBt1nkQPnMD+r0D4D9+pV9+/ovvvPCz/zyPl/jaGwbzd3Kjz3R5PkceB79y0L7+1/Na6+bg+jv5e/Pm"
    "7JorFemvF+29kL4c/288dNx88uHHT96/F72kuTZSCGlYjaNjbRDbibP6EnZTWT1LGj92+uLQI+tOJUmPsIfo0ztEWb2z/k7G"
    "6AL7B8/rUmAk3kjdVWX1vYhnL9MuyEdJwIRGlPahv10brbk/tHxmdU+979mkjXfZrWW3Kh6J8MibIpjCdJrVPUbcY+h+ZtAc"
    "Md+bsdMeGwPusfkkcEYraVmp62qHFwV7/Mp37zE/+YUyzN3pFdig2a0z6rV3rKCBVsXFi+kwk7GwZzhbscxHHfcwux/8ImXY"
    "XY7beunrP7Ol+/RjwGBGXQEQf7A0XkZaHcljXS/dGTGZezDaByysN1F3SUBnbSTn/vCJ2dhza8BsT942QcAM4G4da6M+94d3"
    "3zH3hNb+xNRwFf2aT3PPOKzdYW4GrE3UuVFnebl8RoXgfCtTNr/pwfd6CyqlVXkz9bDKbdGqfCV7s1YrfsWKdn1/15MzoiUY"
    "BXnT1yuQpQC4461fJCSlgISt4LDcA6aIqmlDYK8kl9KuspbSrsSG9oxxqihPtPeDs5xRo6W2HT4XSYjB3DPejvVqcJsmD7/y"
    "8v4/n73//QcXNv1fqcfz9Rd/fOHy8prUQPUyPP/1+NUfvnAxKwd7M08/QhSc+3hB4dP764wXPr2/ztTOGYXnJehl1LMixtW7"
    "rZf5PXn9ny/MKPyVLMEvKPHT4nGNb76oQ71YnoceWH36wVf3LzAT+Fjt7eEsrut4wDh2uTcfYj7LQjBRbohDOAQecvk2ZOGv"
    "dqmVOwJwisDn5ZvslXLBa7rNliMNRModMRLdx7HvKg5V4PPSUivz6Wu9Wk1Q3GDJlrVqb05ncWdC3gpkT5eIuGhMGV/HiQs6"
    "lfU1MRuzLNPTgjePs40TK5bWOHefuOhbeDtZ5r6Cvpah31W91nltGk6iyTI7UPGmtdJtEH0K8ait8z3sZPjr00y5Ak/bJRDO"
    "y/RUL4G9D7X3ueG68D53tnfHN50dN+rfpX9xvjQs83kZ75QOfdNBq4oDf5+70K34d52GFpMDmXT5XDTm3DiPRbIxacyF98iz"
    "vmNtMnYsPDkNurkML+LppD6LaD5pLsSXPIlHi3Rhkj6SPBeSQ6V/I/pX5/ug+fpcFsn2JFqR/DSSn75IpybxaNG3JvH0G8a5"
    "1jvA7Do6Iz9gZq5jLd759tOPbmItZKkoA+J1mV6VWxKNE6gVZisLXA2VqqQR0ay69IpHoGaIfpdxqj0pX+WNYjVbNSPspqtZ"
    "XYiTrAUqegjcLFSoWszAZfzSEGeYBHazWAvu+oPAwWI8qtzSavhUDTCLQeYbbPzSYWqDwKrqh+AWJ83RvxV2mE6VPDXgKXkx"
    "GzcLpSoN7Ziv3elXuaWKRpMs7FQaqtqDF6b21UJtMKaMnwXnuIjOZp5qQGgR5mV0KB2xH0Vw6IJPFTiJ2HXlr5nvWoEncBO1"
    "bIYnfptpHPFwho5xNBalCqzme0gf3aJh7hbCVQZkQHmksQoqhx6XWytiObS9W0yF4rllQPBpAh+LcLC4YsUnkKwGcU/VA3g2"
    "w2friMuGxh4b7GYdMu9jCv0byTbkfNG3nC8aCuayOknepB28tlgXlSt9pEX1Rd/eqgV0wJg2rzLwXZXPNkmnbJmsBbrQDE81"
    "zc73ZPTc35LvOn83bW0r4/hARybR3OhQOvR3y3PY8qOhbNWW4aC643KeEBszlBeTdH/R3CfJ2KK5yLzcbmhMOOiZ0KdZ7JDb"
    "w+Z64XZvkmyTrStzw3HRbyfZWNsGlbGPLkVCIV3G2qS5L8JZ8ByOv+s+yeexqI/0V94p3ZrRYevyIhmbJDOLfmvLqtrnDVN7"
    "XaSzFltVK9kfisGrmfBX2+t2mOhTSB+r29WIWKnhdsxt2qQ+i3CYJGML+QWwe53a3QbaMl/rld1j/pZFtnGS7hAfE/El03qU"
    "yO4F+e5B+Piaq1uxatv3w9td1ybp8iKbP0nXiF91kswvWnMnra2EfyX8VR4S6UskfQku5647i2zFJNtO42cavy4ac5KtW7SG"
    "TlrLbtaFYvzaNuReO9tPGv/eugP4apt1kSo14cGcFPkhJ0WOqNyjT+oWKX4T8XwvKv1kTZkaeK47S/vAk8xa6UefJJfCORe4"
    "WblIgVGKUODDSsBljeMq6JOspJ7DQ54E1ooKB54HRnWFbJUW7HlylLXMCaVKu+EfE54kD1aaUp4QRpnErIHd2Z/3Rvm7HBC3"
    "VuUZ6WzlXpOsIFryMXVUMKp4ghol++7BleBilZkc1mfXs1VjAhzwnDn3qQ+MX7z/AKxPX2u1pyDPOUep5KRwFjgKrIWO9Inu"
    "6rxzeXg4U+YXXz355Z80Vu3Zn964+8ebz//w/tN3//shl41klLz/+LXvPn71e89f+cgfsnn67qMXvmKzez9+7U0PbLPnbD6S"
    "Mk76ls17N2/ZhFa5rvLp6dP74+u6yl9/8au7P75z6335i1xGvHuTxXPteTkfRVCmXY/6/y8x6MXxb7/5/U06NWQmmwwke85A"
    "ZUDbszrs5JSR1BEgepEanks429V5IatGktVKnXe7vzzvnc1xKc+Ww3GpNkGrAeS6y9pnytZPDdUJ9Al5xfN8ul7uy7I+De44"
    "rP3b4ONIAsP+lny3WCWWnHE7GBfsmFbqyBFVAjqePEeVgBxAt4qnxEGfDZutUHqqXmTZ8WaKGc5lR4OrLdL4YcD2jLpXVd/0"
    "WYZ/Bw3xXMLaeBazXVo5ZOPg8wp4Bt6j+nPZWQY572cONs6LaOV063jevlk2gc+lLMJhkgwQnoNou+mgz7fnHcW9v+Uy0/15"
    "e8Rwbr7TOIPo2RbNcRJt1x6zzk3b7PzSNcJpsojmk+ZO43TCs4rMJJcNlx/iY6bvpkX6JbqmT64ofTLxy7MedN3x8ZPrrOvL"
    "3Po+SPe5vS+i+aS5L5KZSTrCO4dkD6W0K2f107ffe/qjf7/vn+k7RUfdQ1o3TF1RWlss9v0gwu4vfbzSZLT7m2B7aa3Vo+f6"
    "JBqXIsK7ulxdWKTLbj8tTNipbin47druE/23on2x+tXUhg8ZZ9ijJMkeWdD+nnoULTq3mJtV66jsPst+K3WrfMxqPijvn60e"
    "kX9L8Uyes1N3ruvGedFcHM8MWh0WBZ3sUq6aH+beOPpdCxciOi/7bcOVD2iycNWkqWXp2HVjtgxM+pbzJYIvbsn1SknrSjnv"
    "Ms33mEQr4mMmPNV97/VJkt3kHYR/mRvO1J6pPRL9M/E9UXuldh0nmgzrlZh/1/XCYe0fiG5b3g4a5zDdke96BKDD3B6m8Tpj"
    "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"
    "as9XaEVxWJzDnMfFf/mX/wPAMMp/"
)
VERIFIED_MAP = json.loads(decompress(b64decode(VERIFIED_MAP_DATA)))

# Shared land boundaries in the app's prefecture geometry.
LAND_NEIGHBORS = {
    row[:2]: row.split()[1:] for row in """
02 03 05
03 02 04 05
04 03 05 06 07
05 02 03 04 06
06 04 05 07 15
07 04 06 08 09 10 15
08 07 09 11 12
09 07 08 10
10 07 09 11 15 20
11 08 10 12 13 19 20
12 08 11 13
13 11 12 14 19
14 13 19 22
15 06 07 10 16 20
16 15 17 20 21
17 16 18 21
18 17 21 25 26
19 11 13 14 20 22
20 10 11 15 16 19 21 22 23
21 16 17 18 20 23 24 25
22 14 19 20 23
23 20 21 22 24
24 21 23 25 26 29 30
25 18 21 24 26
26 18 24 25 27 28 29
27 26 28 29 30
28 26 27 31 33
29 24 26 27 30
30 24 27 29
31 28 32 33 34
32 31 34 35
33 28 31 34
34 31 32 33 35
35 32 34
36 37 38 39
37 36 38
38 36 37 39
39 36 38
40 41 43 44
41 40 42
42 41
43 40 44 45 46
44 40 43 45
45 43 44 46
46 43 45
""".strip().splitlines()
}
# Nearby coasts across straits and bays. Okinawa uses an inset in MAP.
SEA_NEIGHBORS = {}
for first, second in (
    ("01", "02"), ("12", "14"), ("28", "36"), ("33", "37"),
    ("34", "38"), ("35", "40"), ("41", "43"), ("42", "43"),
):
    SEA_NEIGHBORS.setdefault(first, []).append(second)
    SEA_NEIGHBORS.setdefault(second, []).append(first)


# One documented example tied to the industry taught for each prefecture.
# Examples may be regional products, named varieties, individual products or local dishes.
CORE_RIVERS = set("""
石狩川 天塩川 岩木川 北上川 雄物川 米代川 最上川 阿武隈川 那珂川 鬼怒川
利根川 荒川 多摩川 相模川 信濃川 阿賀野川 庄川 黒部川 手取川 九頭竜川
富士川 木曽川 大井川 天竜川 矢作川 宮川 淀川 大和川 熊野川 紀の川
千代川 斐伊川 旭川 吉井川 太田川 江の川 吉野川 肱川 渡川 筑後川
球磨川 大野川 大淀川 川内川
""".split())
CORE_PEAKS = set("""
大雪山 利尻山 岩木山 岩手山 栗駒山 蔵王山 月山 鳥海山 磐梯山 燧ヶ岳
筑波山 男体山 三本槍岳 赤城山 高尾山 丹沢山 箱根山 妙高山 立山 白山
富士山 赤岳 槍ヶ岳 乗鞍岳 間ノ岳 茶臼山 御在所山 伊吹山 比叡山
六甲山 大台ヶ原山 大山 三瓶山 剣山 石鎚山 英彦山 雲仙岳 阿蘇山
くじゅう連山 霧島山 祖母山
""".split())

# Sea names use coastal reference points in latitude and longitude.
# Inland prefectures have no sea labels. Keep enclosed seas distinct from ocean-facing shores.
SEA_AREAS = {
    "太平洋": """
01:41.8,144.5 02:40.8,142.3 03:39.5,142.3 04:38.82,142.15 07:37.5,141.65
08:36.35,141.2 12:35.55,141.15 13:34.45,140.4 14:34.95,139.45
22:34.6,138.95 23:34.39,137.2 24:34.02,137.2 30:33.5,135.6 36:33.65,134.95
39:33.13,133.65 45:32.0,132.02 46:30.62,131.15 47:25.5,128.7
""",
    "日本海": """
01:43.5,138.5 02:40.9,139.7 05:39.75,139.1 06:38.75,139.2 15:38.2,138.18
16:37.1,137.38 17:37.45,136.1 18:36.05,135.65 26:35.92,135.18 28:35.88,134.72
31:35.82,134.08 32:35.8,132.9 35:34.73,131.15 40:34.0,130.2
""",
    "瀬戸内海": """
27:34.62,135.14 28:34.52,134.52 33:34.43,134.1 34:34.13,132.85 35:33.73,132.02
36:34.3,134.68 37:34.54,133.78 38:34.12,132.89 40:33.86,131.24 44:33.61,131.89
""",
    "オホーツク海": "01:45.05,144.3",
    "東シナ海": "42:32.65,128.78 43:32.23,129.88 46:31.55,129.65 47:27.3,126.2",
    "有明海": "40:33.03,130.37 41:33.04,130.23 42:32.84,130.35 43:32.69,130.33",
    "東京湾": "12:35.51,139.83 13:35.57,139.88 14:35.37,139.83",
    "伊勢湾": "23:34.78,136.8 24:34.69,136.8",
}
SEA_LABELS = {}
for sea, sites in SEA_AREAS.items():
    for site in sites.split():
        pid, lat_lon = site.split(":")
        SEA_LABELS.setdefault(pid, []).append(dict(name=sea, point=project(pid, lat_lon)))

# Original, source-hosted photographs: the default row is the regional specialty.
LAND_ROWS = """
01|area|43.12,144.51 43.20,144.31 43.51,144.26 43.78,144.65 43.68,145.01 43.53,145.10 43.37,145.34 43.16,145.47 43.06,144.93
02|area|40.53,140.42 40.58,140.31 40.86,140.30 41.03,140.29 41.06,140.50 40.82,140.55 40.63,140.64
04|area|37.97,140.89 38.10,140.79 38.27,140.88 38.37,141.00 38.36,141.13 38.20,141.11 37.97,140.96
05|area|39.04,140.47 39.13,140.38 39.30,140.38 39.52,140.39 39.59,140.47 39.50,140.60 39.24,140.64 39.07,140.56
06|area|38.18,140.30 38.32,140.21 38.53,140.24 38.62,140.34 38.44,140.43 38.25,140.40
07|area|37.72,140.43 37.77,140.32 37.86,140.44 37.88,140.58 37.77,140.58
08|water|36.10,140.28 36.08,140.35 36.12,140.39 36.08,140.44 36.04,140.43 35.99,140.51 35.96,140.63 35.93,140.56 35.97,140.47 35.99,140.40 36.03,140.36 36.06,140.34 36.07,140.27
09|area|37.17,139.97 37.12,139.88 37.03,139.91 36.94,140.03 37.00,140.12 37.11,140.06
10|area|36.46,138.44 36.49,138.30 36.59,138.35 36.62,138.54 36.55,138.64 36.48,138.55
11|river|36.18,138.96 36.22,139.08 36.25,139.13 36.28,139.20 36.27,139.28 36.23,139.37 36.20,139.45 36.15,139.56 36.16,139.67 36.13,139.76 36.10,139.84
12|coast|35.69,140.71 35.64,140.64 35.58,140.56 35.51,140.48 35.44,140.43 35.36,140.39
13|area|35.77,139.33 35.78,139.36 35.78,139.41 35.77,139.46 35.75,139.43 35.75,139.37
14|water|35.27,139.11 35.29,139.30 35.30,139.52 35.23,139.66 35.01,139.52 34.96,139.23 35.10,139.10
15|area|37.44,138.78 37.61,138.72 37.79,138.87 37.98,139.03 38.17,139.39 38.00,139.48 37.80,139.27 37.61,139.07 37.45,138.92
16|area|36.52,136.87 36.57,136.80 36.73,136.86 36.75,136.99 36.64,137.09 36.54,137.05
17|water|36.65,136.63 36.69,136.64 36.71,136.69 36.68,136.71 36.65,136.70 36.63,136.67
18|coast|36.05,136.00 35.98,135.96 35.92,135.95 35.88,135.96 35.82,136.00 35.78,136.05 35.72,136.02
19|area|35.54,138.49 35.63,138.44 35.71,138.54 35.71,138.74 35.65,138.79 35.55,138.65
20|river|35.97,138.60 36.01,138.54 36.04,138.50 36.12,138.47 36.22,138.48 36.32,138.44 36.39,138.32 36.47,138.19 36.55,138.14 36.59,138.20 36.66,138.24 36.72,138.30 36.80,138.38 36.85,138.37 36.92,138.43 36.98,138.54 37.01,138.59
21|river|36.03,136.91 35.95,136.90 35.86,136.88 35.75,136.93 35.67,136.93 35.60,136.91 35.55,136.80 35.48,136.78 35.44,136.78 35.41,136.73 35.35,136.72 35.27,136.66 35.17,136.67 35.10,136.67
22|area|34.69,138.03 34.78,138.01 34.89,138.09 34.93,138.18 34.85,138.21 34.75,138.15 34.68,138.08
23|area|34.57,137.01 34.59,137.02 34.65,137.09 34.70,137.24 34.73,137.39 34.66,137.40 34.61,137.25 34.56,137.13
24|water|34.30,136.73 34.34,136.79 34.33,136.84 34.31,136.87 34.26,136.82 34.25,136.78
25|water|35.15,135.92 35.24,135.94 35.32,136.04 35.43,136.06 35.50,136.16 35.42,136.26 35.33,136.26 35.24,136.19 35.16,136.07 35.07,135.95 35.01,135.89 35.05,135.87
26|river|34.95,135.94 34.90,135.90 34.89,135.87 34.89,135.82 34.92,135.80 34.92,135.76 34.91,135.70
27|area|34.42,135.28 34.56,135.38 34.72,135.42 34.85,135.49 34.86,135.65 34.74,135.68 34.61,135.68 34.48,135.56 34.37,135.37
28|area|34.16,134.60 34.34,134.64 34.64,134.93 34.66,135.06 34.51,135.03 34.25,134.95 34.16,134.82
29|river|34.34,136.01 34.32,135.94 34.33,135.90 34.33,135.82 34.40,135.77 34.39,135.73 34.35,135.69 34.34,135.63 34.32,135.58
30|river|34.23,135.59 34.18,135.52 34.14,135.48 34.10,135.43 34.08,135.39 34.06,135.34 34.07,135.27 34.08,135.23 34.09,135.17 34.09,135.10
31|area|35.54,134.20 35.55,134.22 35.55,134.26 35.54,134.27 35.53,134.25 35.53,134.22
32|water|35.42,132.83 35.46,132.83 35.48,132.94 35.47,133.03 35.45,133.05 35.41,133.00 35.40,132.90
33|area|34.49,133.72 34.60,133.68 34.72,133.83 34.73,133.96 34.67,134.11 34.54,134.11 34.46,133.91
34|water|34.10,132.20 34.27,132.24 34.38,132.37 34.37,132.48 34.27,132.58 34.13,132.52 33.99,132.37
35|water|33.94,130.86 33.97,130.92 33.96,130.96 33.99,131.00 33.96,131.02 33.93,130.97 33.92,130.91
36|river|34.04,133.83 34.03,133.93 34.05,134.01 34.05,134.11 34.06,134.19 34.08,134.26 34.06,134.34 34.09,134.40 34.11,134.45 34.10,134.54 34.09,134.61
37|area|34.10,133.64 34.12,133.61 34.18,133.66 34.24,133.71 34.23,133.75 34.14,133.75 / 34.19,133.79 34.22,133.78 34.30,133.76 34.31,133.83 34.34,133.90 34.30,133.96 34.24,133.98 34.18,133.91 34.15,133.87 / 34.23,134.00 34.31,133.98 34.37,134.05 34.36,134.13 34.31,134.20 34.25,134.19 34.20,134.10
38|water|33.01,132.22 33.15,132.23 33.33,132.27 33.49,132.39 33.48,132.47 33.33,132.52 33.16,132.51 32.98,132.47
39|area|33.46,133.40 33.56,133.41 33.59,133.53 33.58,133.68 33.53,133.76 33.47,133.68 33.47,133.53
40|area|33.03,130.37 33.18,130.36 33.31,130.45 33.41,130.59 33.36,130.72 33.23,130.68 33.13,130.59 33.01,130.50
41|water|33.24,130.18 33.17,130.32 33.03,130.43 32.87,130.48 32.72,130.38 32.73,130.24 32.90,130.14 33.09,130.10
42|water|33.10,129.56 33.23,129.52 33.28,129.58 33.24,129.68 33.14,129.70 33.07,129.66
44|area|33.40,131.48 33.54,131.36 33.67,131.46 33.69,131.64 33.57,131.74 33.43,131.69
45|area|31.84,131.37 31.92,131.31 32.03,131.32 32.15,131.40 32.24,131.49 32.19,131.56 32.04,131.55 31.87,131.48
46|area|31.16,130.28 31.28,130.20 31.50,130.21 31.63,130.30 31.62,130.57 31.44,130.62 31.22,130.66 31.13,130.57
47|area|26.03,127.61 26.08,127.95 26.30,127.94 26.40,128.06 26.65,128.26 26.86,128.35 26.89,128.18 26.72,128.00 26.55,127.84 26.43,127.68 26.21,127.60
"""

def land_overlay(pid, kind, rings):
    path = []
    for ring in rings.split("/"):
        coordinates = [",".join(map(str, project(pid, point))) for point in ring.split()]
        path.append("M"+"L".join(coordinates)+("Z" if kind in ("area", "water") else ""))
    return {"kind":kind, "path":"".join(path)}


LAND_OVERLAYS = {}
for row in LAND_ROWS.strip().splitlines():
    pid, kind, rings = row.split("|")
    LAND_OVERLAYS[pid] = land_overlay(pid, kind, rings)

# The same main channel is called Chikuma in Nagano and Shinano in Niigata.
chikuma = next((river for river in VERIFIED_MAP["20"]["rivers"] if river["name"] == "信濃川"), None)
if chikuma:
    LAND_OVERLAYS["20"] = {"kind":"river", "path":chikuma["path"], "alias":chikuma["name"]}


# Other industries and specialties to discover after the main lesson.
# Question identities needed to validate already recorded version-3 rounds.
ARCHIVE_QUESTIONS_V3 = {
    '01': ('geography.discovery.01.land', 'geography.discovery.01.product'),
    '02': ('geography.discovery.02.land', 'geography.discovery.02.product'),
    '03': ('geography.discovery.03.land', 'geography.discovery.03.product'),
    '04': ('geography.discovery.04.land', 'geography.discovery.04.product'),
    '05': ('geography.discovery.05.land', 'geography.discovery.05.product'),
    '06': ('geography.discovery.06.land', 'geography.discovery.06.product'),
    '07': ('geography.discovery.07.land', 'geography.discovery.07.product'),
    '08': ('geography.discovery.08.land', 'geography.discovery.08.product'),
    '09': ('geography.discovery.09.land', 'geography.discovery.09.product'),
    '10': ('geography.discovery.10.land', 'geography.discovery.10.product'),
    '11': ('geography.discovery.11.land', 'geography.discovery.11.product'),
    '12': ('geography.discovery.12.land', 'geography.discovery.12.product'),
    '13': ('geography.discovery.13.land', 'geography.discovery.13.product'),
    '14': ('geography.discovery.14.land', 'geography.discovery.14.product'),
    '15': ('geography.discovery.15.land', 'geography.discovery.15.product'),
    '16': ('geography.discovery.16.land', 'geography.discovery.16.product'),
    '17': ('geography.discovery.17.land', 'geography.discovery.17.product'),
    '18': ('geography.discovery.18.land', 'geography.discovery.18.product'),
    '19': ('geography.discovery.19.land', 'geography.discovery.19.product'),
    '20': ('geography.discovery.20.land', 'geography.discovery.20.product'),
    '21': ('geography.discovery.21.land', 'geography.discovery.21.product'),
    '22': ('geography.discovery.22.land', 'geography.discovery.22.product'),
    '23': ('geography.discovery.23.land', 'geography.discovery.23.product'),
    '24': ('geography.discovery.24.land', 'geography.discovery.24.product'),
    '25': ('geography.discovery.25.land', 'geography.discovery.25.product'),
    '26': ('geography.discovery.26.land', 'geography.discovery.26.product'),
    '27': ('geography.discovery.27.land', 'geography.discovery.27.product'),
    '28': ('geography.discovery.28.land', 'geography.discovery.28.product'),
    '29': ('geography.discovery.29.land', 'geography.discovery.29.product'),
    '30': ('geography.discovery.30.land', 'geography.discovery.30.product'),
    '31': ('geography.discovery.31.land', 'geography.discovery.31.product'),
    '32': ('geography.discovery.32.land', 'geography.discovery.32.product'),
    '33': ('geography.discovery.33.land', 'geography.discovery.33.product'),
    '34': ('geography.discovery.34.land', 'geography.discovery.34.product'),
    '35': ('geography.discovery.35.land', 'geography.discovery.35.product'),
    '36': ('geography.discovery.36.land', 'geography.discovery.36.product'),
    '37': ('geography.discovery.37.land', 'geography.discovery.37.product'),
    '38': ('geography.discovery.38.land', 'geography.discovery.38.product'),
    '39': ('geography.discovery.39.land', 'geography.discovery.39.product'),
    '40': ('geography.discovery.40.land', 'geography.discovery.40.product'),
    '41': ('geography.discovery.41.land', 'geography.discovery.41.product'),
    '42': ('geography.discovery.42.land', 'geography.discovery.42.product'),
    '43': ('geography.discovery.43.land', 'geography.discovery.43.product'),
    '44': ('geography.discovery.44.land', 'geography.discovery.44.product'),
    '45': ('geography.discovery.45.land', 'geography.discovery.45.product'),
    '46': ('geography.discovery.46.land', 'geography.discovery.46.product'),
    '47': ('geography.discovery.47.land', 'geography.discovery.47.product'),
}
ARCHIVE_QUESTION_SKILLS = ("map", "industry")

# Each row begins with a map landmark and explains the link between place and activity.
# The first two cards for each prefecture have a question and two comparable alternatives.
EXAM_INDUSTRY_ROWS = """
01|畑作|十勝平野の畑作|とかちへいやのはたさく|帯広市周辺|42.92,143.20|広く平らな畑で、大型機械を使って小麦・じゃがいも・てんさい・豆を栽培する。畑ごとに作る物を年ごとに替える輪作は、同じ作物を作り続けたときの病害などを抑える工夫。
01|畜産|根釧台地の酪農|こんせんだいちのらくのう|別海町周辺|43.39,145.12|夏も涼しく、海からの霧が入る根釧台地では、広い草地で牧草を育てて乳牛を飼う。生乳は飲用のほか、バターやチーズの原料にもなる。
01|稲作|石狩平野の米|いしかりへいやのこめ|岩見沢市周辺|43.20,141.77|石狩川流域では湿地の排水や品種改良が進み、稲作が広がった。北海道の中でも、十勝の畑作や根釧の酪農とは土地の使い方が異なる。
01|漁業|ホタテガイ|ほたてがい|オホーツク海沿岸・紋別市|44.36,143.36|オホーツク海沿岸では、稚貝を海底にまいて大きく育った貝を漁獲する方式がある。青森の陸奥湾で貝をつるして育てる方式と比べられる。
02|果樹|りんご|りんご|弘前市周辺|40.60,140.46|岩木山のふもとなど、津軽地方にりんご園が広がる。涼しい気候を生かし、収穫後は低温で貯蔵して出荷時期を調整する。
02|水産養殖|ホタテガイ養殖|ほたてがいようしょく|陸奥湾・平内町沖|40.96,140.89|陸奥湾は外海より波が穏やかで、稚貝をかごやロープにつるして育てやすい。湾の内側で営む養殖と、外海で行う漁業を地図で比べよう。
03|水産養殖|わかめ養殖|わかめようしょく|三陸海岸・大船渡湾|39.02,141.74|三陸のリアス海岸は入り江が多い。外海より波が穏やかな湾で、海面近くに張ったロープにわかめを育てる。
03|伝統工芸|南部鉄器|なんぶてっき|盛岡市周辺|39.70,141.15|盛岡や奥州で受け継がれてきた鋳物。溶かした鉄を型に流し込み、鉄瓶やなべなどを作る。
04|稲作|大崎平野の米|おおさきへいやのこめ|大崎市・古川周辺|38.57,140.96|大崎平野に水田が広がる。川の水を用水路で田に引き、低地では排水も工夫して米を育てる。
04|水産養殖|カキ養殖|かきようしょく|松島湾周辺|38.36,141.08|松島湾や石巻周辺では、カキの稚貝を付けた資材を海につるして育てる。入り江の多い地形が養殖場の立地に関わる。
05|稲作|秋田平野の米|あきたへいやのこめ|秋田市南部・雄物川下流|39.65,140.15|雄物川下流などの平野では水田が広がる。冬に積もった雪が解けて川に流れ、用水路を通して田に水を引く。
05|林業|秋田杉|あきたすぎ|能代市・米代川下流|40.21,140.04|米代川流域の森林資源と木材を運び出しやすい位置を背景に、能代では木材の加工が発達した。杉は建築材などに使われる。
06|果樹|さくらんぼ|さくらんぼ|東根市周辺|38.43,140.39|山形盆地の東根や天童では果樹栽培が盛ん。さくらんぼは実が熟す時期の雨で割れることがあり、雨よけの屋根を使う園地がある。
06|稲作|庄内平野の米|しょうないへいやのこめ|酒田市・庄内平野|38.89,139.88|最上川の下流には広い平野がある。用水・排水を整えた水田で稲作が行われ、酒田は米を運び出す港としても発展した。
07|果樹|桃|もも|福島市・福島盆地|37.78,140.45|阿武隈川流域の福島盆地では桃などの果樹が作られる。収穫した桃は傷みやすいため、選果・箱詰めをして早く出荷する。
07|稲作|会津盆地の米|あいづぼんちのこめ|会津坂下町周辺|37.56,139.82|会津盆地では川から水を引いて稲作を行う。県内でも福島盆地の果樹と会津盆地の稲作のように、作物の分布に違いがある。
08|農産物|メロン|めろん|鉾田市周辺|36.16,140.52|鹿島灘に近い鉾田では、ハウスなどを使って温度や水分を調整しながらメロンを育てる。首都圏の市場へも出荷する。
08|工業地域|鹿島臨海工業地域|かしまりんかいこうぎょうちいき|鹿島港・神栖市|35.93,140.70|陸地を掘り込んで整備した鹿島港は、大型船で原料を運びやすい。周辺に鉄鋼や石油化学の工場が集まった。
08|食品加工|水戸の納豆|みとのなっとう|水戸市周辺|36.37,140.47|大豆を納豆菌で発酵させる加工食品。水戸の名産として知られる。作物としての大豆の産地と、加工食品の名産地は分けて考えよう。
09|農産物|いちご|いちご|真岡市周辺|36.44,140.01|真岡市などでは冬も日照を利用し、ハウスで温度を調整していちごを育てる。屋外では寒い時期にも出荷できる。
09|機械工業|自動車工業|じどうしゃこうぎょう|上三川町周辺|36.47,139.91|県南部には自動車の組立工場や関連工場がある。内陸でも道路を通じて部品を集め、製品を出荷できる。
10|高原野菜|キャベツ|きゃべつ|嬬恋村周辺|36.53,138.51|嬬恋村は標高が高く、夏でも比較的涼しい。平地が暑い時期にキャベツを生産し、東京などの市場に送る。
10|機械工業|自動車工業|じどうしゃこうぎょう|太田市周辺|36.29,139.38|太田市周辺には自動車の組立工場と部品工場が集まる。高速道路などを利用して部品や完成車を運ぶ北関東の内陸工業の例。
11|近郊農業|ねぎ|ねぎ|深谷市周辺|36.20,139.28|深谷周辺では利根川と荒川の間の農地で野菜が生産される。大きな消費地に近く、ねぎなどを首都圏の市場へ出荷できる。
11|機械工業|内陸の自動車工業|ないりくのじどうしゃこうぎょう|寄居町周辺|36.12,139.22|寄居町などに自動車工場がある。県内を通る高速道路は、内陸の工場と部品の供給先や出荷先をつなぐ。
11|茶|狭山茶|さやまちゃ|入間市周辺|35.82,139.36|県西部の入間市や所沢市周辺には茶畑がある。茶の栽培に比較的冷涼な地域で、冬の寒さに備えて栽培を工夫してきた。
12|畑作|落花生（ピーナッツ）|らっかせい、ぴーなっつ|八街市周辺|35.67,140.32|八街市など、下総台地の水はけのよい畑で育てる。花が咲いたあと、実が育つ部分が土に入り、地中でさやができる。
12|工業地域|京葉工業地域|けいようこうぎょうちいき|東京湾岸・市原市|35.54,140.06|千葉県側の東京湾岸に石油精製や化学工業の工場が集まる。大型船で原油を運び、配管で工場同士をつないで原料を受け渡す。
12|漁業|銚子の漁業|ちょうしのぎょぎょう|銚子漁港|35.75,140.86|利根川の河口付近に銚子漁港があり、太平洋でとれたいわしやさばなどが水揚げされる。水揚げ後に冷凍や加工を行う施設もある。
13|工業|印刷・出版|いんさつしゅっぱん|千代田区・文京区周辺|35.71,139.75|出版社や新聞社などが集まり、編集と印刷を近い場所で行いやすかった。大都市では、人や情報の集まりが産業の立地に関わる。
13|近郊農業|小松菜|こまつな|江戸川区周辺|35.71,139.89|江戸川区は小松菜ゆかりの地。都市の中でも畑が残る場所では、鮮度が大事な葉物野菜を近い消費地へ届けられる。
13|サービス業|金融・商業|きんゆうしょうぎょう|丸の内・大手町|35.68,139.77|交通が便利で人や情報が集まる都心には、銀行や企業の本社などが集中する。ものを作る工業とは異なる第三次産業の例。
14|工業地帯|京浜工業地帯|けいひんこうぎょうちたい|川崎市・横浜市の湾岸|35.50,139.74|川崎や横浜の臨海部には鉄鋼や石油化学などの工場が立地する。東京側にもつながる工業地帯で、港から原料を受け入れやすい。
14|近郊農業|だいこん|だいこん|三浦市周辺|35.17,139.63|三浦半島では海の影響で冬も比較的温暖で、冬から春にかけてだいこんを出荷する。東京や横浜が近いことも出荷に便利。
15|稲作|越後平野の米|えちごへいやのこめ|新潟市南部・越後平野|37.80,139.02|信濃川や阿賀野川下流の広い低地に水田が広がる。水を引くだけでなく、低地にたまる水を排水する工夫も稲作を支えてきた。
15|地場工業|燕三条の金属加工|つばめさんじょうのきんぞくかこう|燕市・三条市|37.65,138.93|燕では金属製の食器、三条では刃物や工具などの生産が発達した。小さな工場が工程を分担する地場産業の一例。
16|稲作|砺波平野の米|となみへいやのこめ|砺波市周辺|36.64,136.97|庄川などがつくった扇状地で、水路を整えて水田を開いた。田の中に屋敷林に囲まれた家が点在する散居村の景観が見られる。
16|工業|医薬品工業|いやくひんこうぎょう|富山市周辺|36.70,137.22|家庭に薬を預け、使った分の代金を後で受け取る売薬が富山で発達した。現在の医薬品製造につながる歴史的な背景の一つ。
17|伝統工芸|金沢箔|かなざわはく|金沢市周辺|36.57,136.66|金などの金属を何度も打ち延ばして、ごく薄い箔にする。金箔は仏具や工芸品、建物の装飾などにも利用される。
17|稲作|加賀平野の米|かがへいやのこめ|白山市・手取川下流|36.48,136.56|手取川の扇状地とその周辺では、用水路で水を分けて田をうるおしてきた。川と平野の関係から稲作の広がりを考えられる。
18|地場工業|めがね枠|めがねわく|鯖江市周辺|35.96,136.18|鯖江や福井では、めがね枠の生産が地場産業として発展した。加工、組立、仕上げを行う事業所が地域内に集まる。
18|漁業|越前がに|えちぜんがに|越前町沿岸|35.93,135.99|福井県の港で水揚げされる雄のズワイガニの呼び名。日本海の海底近くにすむカニをとる漁業で、養殖とは異なる。
19|果樹|ぶどう|ぶどう|甲州市・勝沼周辺|35.66,138.73|甲府盆地のふちでは、水はけのよい扇状地などが果樹園に使われる。ぶどうは生食用と、ワインなどの加工用がある。
19|果樹|桃|もも|笛吹市周辺|35.64,138.65|笛吹市周辺では桃畑が広がる。甲府盆地の果樹はぶどうだけでなく、桃も重要で、春の花や夏の収穫時期に景観が変わる。
20|高原野菜|レタス|れたす|川上村周辺|35.98,138.58|川上村などの標高が高い地域では夏でも比較的涼しい。収穫後に冷やし、鮮度を保ったまま大都市へ出荷する。
20|機械工業|精密機械工業|せいみつきかいこうぎょう|諏訪湖周辺|36.05,138.07|諏訪地域では時計などの精密なものづくりが発展し、細かな加工を得意とする工場が集まった。海岸でなくても発達した内陸工業の例。
21|窯業|美濃焼|みのやき|多治見市・土岐市周辺|35.34,137.15|岐阜県南東部の東濃では、陶磁器用の土を利用し、茶わんや皿などの生産が発達した。愛知県の瀬戸焼とは産地を区別する。
21|林業・木工|飛騨の木工|ひだのもっこう|高山市周辺|36.15,137.25|山地が多い飛騨では木材と木を加工する技術を生かし、家具などが作られる。東濃の陶磁器とは、産地も材料も異なる。
22|茶|茶|ちゃ|牧之原台地周辺|34.80,138.19|牧之原台地には茶畑が広がる。水はけのよい台地などで茶を栽培し、摘んだ葉を蒸すなどして加工する。
22|機械工業|楽器・オートバイ|がっき、おーとばい|浜松市周辺|34.75,137.73|浜松では楽器づくりと二輪車工業が発展してきた。静岡県の工業を学ぶときは、牧之原の茶畑と浜松の工業を地図で区別する。
23|機械工業|中京の自動車工業|ちゅうきょうのじどうしゃこうぎょう|豊田市周辺|35.05,137.16|豊田市周辺では部品工場と組立工場が分担して車を作る。完成車は道路を通じて港にも運ばれ、国内外へ出荷される。
23|窯業|瀬戸焼|せとやき|瀬戸市周辺|35.23,137.10|瀬戸では陶磁器に適する土を利用して焼き物の技術が育った。茶わんや皿などの生産を県境近くの美濃焼と比べられる。
24|水産養殖|真珠養殖|しんじゅようしょく|志摩市・英虞湾|34.30,136.81|英虞湾の入り江には波が穏やかな場所がある。そこでアコヤガイを育て、貝の中で真珠をつくらせる。
24|工業|石油化学コンビナート|せきゆかがくこんびなーと|四日市市の伊勢湾岸|34.95,136.64|四日市の港の近くには、石油を精製し、原料を受け取って化学製品を作る工場が集まる。パイプで工場同士をつなぐ。
25|稲作|近江米|おうみまい|彦根市周辺・湖東平野|35.25,136.22|琵琶湖の東側の平野などには水田が広がる。川や湖の水を農業に利用しながら、田から流れる水が湖の水質に与える影響にも配慮する。
25|内水面漁業|琵琶湖の漁業|びわこのぎょぎょう|近江八幡市沖・琵琶湖|35.17,136.01|海のない滋賀県では、琵琶湖でアユの仲間やビワマスなどの漁業が行われる。湖でとれる魚を使った保存食にふなずしがある。
26|茶|宇治茶|うじちゃ|宇治市周辺|34.89,135.81|宇治や京都府南部では茶の栽培・加工が盛ん。玉露や抹茶の原料のてん茶には、収穫前に覆いをかける栽培方法がある。
26|伝統工芸|西陣織|にしじんおり|京都市上京区周辺|35.03,135.74|京都市の西陣では、先に染めた糸を組み合わせて複雑な模様を織る。帯などに使われ、染め・織りなどを分業して作る。
27|工業地帯|阪神工業地帯|はんしんこうぎょうちたい|堺市・大阪湾岸|34.60,135.43|大阪と神戸を中心に広がり、堺の臨海部などに鉄鋼の工場がある。港と都市の市場を利用した工業が集まる。
27|地場工業|町工場の部品づくり|まちこうばのぶひんづくり|東大阪市周辺|34.67,135.59|東大阪には、金属を削る、曲げる、ねじを作るなど、それぞれの加工が得意な工場が集まる。近い工場同士で工程を分担しやすい。
28|機械工業|造船業|ぞうせんぎょう|神戸港周辺|34.66,135.19|神戸港周辺では船を造る工業が発達した。大きな船を直接海へ出せる岸壁が必要で、港の近くに立地する。
28|農産物|たまねぎ|たまねぎ|南あわじ市周辺|34.30,134.79|淡路島南部では、田で米を作ったあとにたまねぎを育てる例がある。温暖な気候を生かし、収穫後は乾燥させて出荷する。
29|林業|吉野の林業|よしののりんぎょう|吉野町・川上村周辺|34.36,135.93|吉野川の上流では杉やヒノキを植え、枝打ちや間伐をしながら長い年月をかけて育ててきた。建築材として使われる。
29|果樹|柿|かき|五條市周辺|34.35,135.69|五條市など吉野川沿いの斜面では柿を栽培する。日当たりや水はけを考えて果樹園の場所が選ばれている。
30|果樹|みかん|みかん|有田市周辺|34.08,135.13|有田川流域では温暖な気候と、日当たり・水はけのよい斜面を利用してみかんを育てる。海岸近くの段々畑も産地の目印。
30|果樹・加工|梅|うめ|みなべ町周辺|33.77,135.32|みなべ・田辺では斜面などに梅林が広がる。収穫した梅は塩漬けや天日干しなどの工程を経て梅干しになる。
31|果樹|なし|なし|倉吉市周辺|35.44,133.82|鳥取では二十世紀梨が長く栽培され、倉吉市などに果樹園がある。実に袋をかけて、傷や病害などを防ぐ工夫をする。
31|砂丘農業|らっきょう|らっきょう|鳥取市・福部砂丘|35.53,134.31|砂は水はけがよく乾きやすい。福部地区では水の管理をしながら砂丘地でらっきょうを育てて出荷する。
32|内水面漁業|ヤマトシジミ|やまとしじみ|松江市・宍道湖|35.44,133.00|宍道湖には川の淡水と中海から来る海水が混ざる。このような汽水の湖で、ヤマトシジミがとれる。
32|稲作|出雲平野の米|いずもへいやのこめ|出雲市・斐川町周辺|35.39,132.81|斐伊川下流の出雲平野では水田が広がる。同じ水辺でも、宍道湖の漁業と平野の稲作では水の使い方が違う。
33|工業地域|水島の臨海工業|みずしまのりんかいこうぎょう|倉敷市・水島|34.51,133.74|水島港の近くには製鉄、石油化学、自動車などの工場が集まる。大型船で原料や製品を運びやすい瀬戸内工業地域の一角。
33|果樹|白桃|はくとう|岡山市・一宮周辺|34.69,133.86|岡山県南部では比較的降水量が少なく、桃などの果樹栽培が行われる。白い果皮に仕上げるため袋をかけて育てる例がある。
34|機械工業|自動車工業|じどうしゃこうぎょう|広島市・府中町周辺|34.38,132.50|広島市と周辺に組立工場や部品工場が集まり、完成車は港からも出荷される。瀬戸内の海上輸送を利用する機械工業の例。
34|水産養殖|カキ養殖|かきようしょく|広島湾・江田島市周辺|34.26,132.46|広島湾では、いかだからカキをつるして育てる。島や入り江が多く、波の穏やかな水域を養殖に利用できる。
35|工業|周南の石油化学|しゅうなんのせきゆかがく|周南市・徳山湾岸|34.05,131.81|周南の湾岸では石油化学工場の集積がみられる。船で原料を受け入れ、工場が原料や製品を受け渡す瀬戸内工業地域の例。
35|水産流通|ふぐ|ふぐ|下関市・南風泊|33.95,130.91|下関には各地でとれたふぐや養殖されたふぐも集まる市場がある。水揚げ・集荷の場所と、魚をとった場所は同じとは限らない。
36|果樹|すだち|すだち|神山町周辺|33.97,134.35|神山町など、徳島の山あいで栽培されるかんきつ。完熟前の緑色の実も出荷され、香りや酸味を料理に添える。
36|水産養殖|鳴門わかめ|なるとわかめ|鳴門海峡周辺|34.22,134.60|鳴門海峡周辺ではロープを使ってわかめを育てる。海峡の潮の流れが速い海域を利用した水産養殖の例。
37|稲作|ため池を使う稲作|ためいけをつかういなさく|満濃池・まんのう町|34.15,133.89|讃岐平野は降水量が比較的少なく、大きな川が少ない。ため池に水を蓄えて水田に送り、現在は香川用水から来る水も使う。
37|食品加工|讃岐うどん|さぬきうどん|高松市周辺|34.33,134.04|小麦粉をこねて麺にする香川の食文化。小麦が作られてきた地域だが、うどんの原料には県外産や輸入小麦も使われる。
37|果樹|オリーブ|おりーぶ|小豆島町周辺|34.48,134.27|小豆島では、瀬戸内の比較的雨が少なく日照の多い環境を生かしてオリーブを栽培する。実から油をしぼることもできる。
38|果樹|みかん|みかん|八幡浜市周辺|33.46,132.42|宇和海沿いなどの傾斜地で、日当たりと水はけを生かしたかんきつ栽培を行う。険しい斜面を段々畑にした場所もある。
38|機械工業|今治の造船|いまばりのぞうせん|今治市沿岸|34.07,133.00|今治の沿岸には船を建造する造船所が立地する。瀬戸内海は島の間を船が行き来し、船を運航する事業も発達してきた。
38|水産養殖|真珠養殖|しんじゅようしょく|宇和島市・宇和海沿岸|33.24,132.49|宇和海の波が穏やかな入り江などでアコヤガイを育てて真珠をつくる。みかんを育てる斜面と、養殖を行う海が近い地域もある。
39|施設園芸|なすの促成栽培|なすのそくせいさいばい|安芸市周辺|33.50,133.91|高知は冬も比較的温暖で日照に恵まれる。ハウスで温度を調整し、露地での出荷が少ない時期にもなすを出す促成栽培を行う。
39|漁業|カツオ漁|かつおりょう|中土佐町・久礼漁港|33.33,133.23|高知は黒潮が流れる太平洋に面し、カツオの一本釣りなどが知られる。カツオのたたきのように、漁業が食文化にもつながる。
40|工業|北九州の鉄鋼業|きたきゅうしゅうのてっこうぎょう|北九州市・八幡周辺|33.88,130.81|八幡には明治期に官営製鉄所が建設された。筑豊の石炭を利用しやすいことと、港で原料を運べることが発展に関わった。
40|農産物|いちご|いちご|八女市・筑後平野|33.21,130.56|筑後地方では、ハウスの温度管理をしながらいちごを育てる。福岡は米や野菜も作るため、地域と栽培方法を結びつけて考えよう。
41|水産養殖|のり養殖|のりようしょく|佐賀市南部・有明海|33.13,130.29|有明海は潮の満ち引きの差が大きい。海に張った網にのりを育て、潮が引くと網が空気に触れる時間も利用する。
41|窯業|伊万里・有田焼|いまりありたやき|有田町・伊万里市周辺|33.18,129.89|有田では陶石を使った磁器の生産が発達した。焼き物の一部は伊万里の港から積み出され、国内外に運ばれた。
42|果樹|びわ|びわ|長崎市・茂木周辺|32.69,129.92|長崎市の茂木などでは、海沿いの比較的温暖な斜面を生かしてびわを栽培する。実は傷がつきやすく、丁寧に扱って出荷する。
42|機械工業|造船業|ぞうせんぎょう|長崎港周辺|32.74,129.85|奥深い長崎港に面して、船を造って修理できる施設が発達した。大型船を海へ出せる港が工場の立地に関わる。
43|畜産|肉牛の放牧|にくぎゅうのほうぼく|阿蘇市・阿蘇の草原|32.99,131.08|阿蘇の草原では肉用牛などを放牧する。人が草を刈り、野焼きなどで管理することも草原の維持につながっている。
43|施設園芸|トマト|とまと|八代市周辺|32.50,130.57|八代平野などでは、ハウスで温度を管理してトマトを育てる。冬から春の出荷が、夏の露地栽培が中心の産地を補う。
44|林産物|原木しいたけ|げんぼくしいたけ|豊後大野市周辺|32.98,131.58|クヌギなどの丸太にしいたけの菌を植え付け、林の中などで育てる。収穫後に乾燥させた干ししいたけは保存しやすい。
44|工業|臨海部の鉄鋼業|りんかいぶのてっこうぎょう|大分市・別府湾岸|33.26,131.68|大分市の臨海部には製鉄所が立地する。鉄鉱石などの重い原料を海外から大型船で運べる港が工場の立地を支える。
45|施設園芸|ピーマンの促成栽培|ぴーまんのそくせいさいばい|宮崎市・宮崎平野|31.98,131.44|冬も比較的暖かく日照のある宮崎平野で、ハウスを使いピーマンなどを早い時期から出荷する。高知の施設園芸と比較できる。
45|畜産|ブロイラーの飼育|ぶろいらーのしいく|都城市周辺|31.73,131.06|宮崎南西部では畜産が盛んで、肉用の鶏も飼育される。生産農場から食肉処理・加工を経て、鶏肉が各地に運ばれる。
46|畑作・加工|さつまいも|さつまいも|鹿屋市・大隅半島|31.39,130.85|火山の噴出物が積もったシラス台地は水がしみ込みやすい場所がある。大隅半島などでさつまいもを育て、でんぷんや焼酎などにも加工する。
46|畜産|養豚|ようとん|曽於市周辺|31.65,131.00|鹿児島では豚の飼育や食肉加工が盛ん。黒豚はその代表例の一つで、県内の畜産には肉用牛や肉用鶏も含まれる。
46|茶|茶|ちゃ|南九州市・知覧周辺|31.38,130.45|南薩の台地などで茶を栽培する。温暖な気候で春の新茶を早く出せ、まとまった畑では機械を使って収穫する。
47|畑作・加工|さとうきび|さとうきび|南城市周辺・沖縄本島南部|26.15,127.79|亜熱帯の温暖な気候で育つ。茎をしぼった汁から砂糖を作るため、畑と製糖工場が同じ島に立地することが多い。
47|サービス業|観光業|かんこうぎょう|恩納村沿岸|26.49,127.85|温暖な気候やサンゴ礁の海、琉球の歴史・文化を目当てに旅行者が訪れる。宿泊施設や交通、案内などのサービスにつながる。
47|果樹|パイナップル|ぱいなっぷる|東村周辺・沖縄本島北部|26.64,128.12|本島北部などの温暖な地域で育つ。生で食べるほか、加工品にもなる。さとうきびと同じ南の作物でも、使う部分や加工の仕方は異なる。
25|食品加工|ふなずし|ふなずし|高島市周辺・琵琶湖西岸|35.35,136.02|琵琶湖のフナを塩漬けにして米と発酵させる保存食。湖の漁業と周辺の稲作の両方が、食文化に結びついている。
29|果樹|なし|なし|大淀町周辺|34.39,135.81|奈良県内でも大淀町などでなしを作る。吉野川周辺は、林業だけでなく果樹の栽培も見られる。
"""
EXAM_NAME_ROWS = """
01|帯広の周りで、小麦・じゃがいも・てんさいの輪作がさかんな平野は？|十勝平野|とかちへいや|石狩平野|いしかりへいや|庄内平野|しょうないへいや
01|北海道の東部で、夏も涼しく、乳牛を育てる酪農がさかんな台地は？|根釧台地|こんせんだいち|下総台地|しもうさだいち|牧之原台地|まきのはらだいち
02|岩木山のふもとに果樹園が広がる、津軽地方の代表的な果物は？|りんご|りんご|桃|もも|さくらんぼ|さくらんぼ
02|平内町の沖でホタテガイの養殖がさかんな湾は？|陸奥湾|むつわん|松島湾|まつしまわん|英虞湾|あごわん
03|大船渡湾など、岩手県の入り江が多い東側の海岸は？|三陸海岸|さんりくかいがん|九十九里浜|くじゅうくりはま|越前海岸|えちぜんかいがん
03|盛岡などで、溶かした鉄を型に流して鉄瓶などを作る伝統工芸品は？|南部鉄器|なんぶてっき|金沢箔|かなざわはく|西陣織|にしじんおり
04|古川の周りで、水路を使った稲作がさかんな平野は？|大崎平野|おおさきへいや|庄内平野|しょうないへいや|秋田平野|あきたへいや
04|宮城県の、入り江や島が多くカキの養殖がさかんな湾は？|松島湾|まつしまわん|陸奥湾|むつわん|広島湾|ひろしまわん
05|秋田市周辺の水田地帯を流れ、日本海に注ぐ川は？|雄物川|おものがわ|最上川|もがみがわ|手取川|てどりがわ
05|米代川流域から能代へ運ばれ、建築材などに加工されてきた木は？|秋田杉|あきたすぎ|吉野杉|よしのすぎ|ヒノキ|ひのき
06|東根市周辺で、実が雨にぬれて割れないよう屋根を使って育てる果物は？|さくらんぼ|さくらんぼ|りんご|りんご|みかん|みかん
06|酒田市があり、最上川の下流に水田が広がる平野は？|庄内平野|しょうないへいや|秋田平野|あきたへいや|越後平野|えちごへいや
07|阿武隈川流域の福島盆地で、夏に出荷する代表的な果物は？|桃|もも|りんご|りんご|さくらんぼ|さくらんぼ
07|福島盆地の果樹栽培に対して、福島県の西側で稲作がさかんな盆地は？|会津盆地|あいづぼんち|山形盆地|やまがたぼんち|甲府盆地|こうふぼんち
08|鉾田市周辺でハウスなどを使って育てる、果肉が甘いウリの仲間は？|メロン|めろん|いちご|いちご|桃|もも
08|神栖市周辺にあり、掘り込み式の港を利用する工業地域は？|鹿島臨海工業地域|かしまりんかいこうぎょうちいき|京葉工業地域|けいようこうぎょうちいき|京浜工業地帯|けいひんこうぎょうちたい
09|真岡市周辺で、冬のハウス栽培でも出荷する赤い果実は？|いちご|いちご|メロン|めろん|桃|もも
09|栃木県南部にあり、自動車の組立工場が立地する町は？|上三川町|かみのかわまち|寄居町|よりいまち|嬬恋村|つまごいむら
10|嬬恋村で、夏の高原の涼しさを生かして出荷する代表的な野菜は？|キャベツ|きゃべつ|ねぎ|ねぎ|たまねぎ|たまねぎ
10|群馬県の南東部で、自動車の組立工場や部品工場が集まる市は？|太田市|おおたし|豊田市|とよたし|東大阪市|ひがしおおさかし
11|深谷市周辺で育て、首都圏に出荷する代表的な長い野菜は？|ねぎ|ねぎ|キャベツ|きゃべつ|たまねぎ|たまねぎ
11|埼玉県の内陸にあり、自動車工場が立地する町は？|寄居町|よりいまち|上三川町|かみのかわまち|小豆島町|しょうどしまちょう
12|八街市周辺で、花が咲いたあとに地中でさやが育つ作物は？|落花生（ピーナッツ）|らっかせい、ぴーなっつ|いちご|いちご|さつまいも|さつまいも
12|原油を大型船で運べる東京湾の千葉県側に、石油化学工場が集まる工業地域は？|京葉工業地域|けいようこうぎょうちいき|京浜工業地帯|けいひんこうぎょうちたい|鹿島臨海工業地域|かしまりんかいこうぎょうちいき
13|東京都心で出版社や新聞社の近くに発達した、文字や絵を紙に刷る工業は？|印刷業|いんさつぎょう|造船業|ぞうせんぎょう|鉄鋼業|てっこうぎょう
13|江戸川区ゆかりの、近い消費地に新鮮なうちに出荷する葉物野菜は？|小松菜|こまつな|たまねぎ|たまねぎ|だいこん|だいこん
14|川崎・横浜の臨海部を含み、鉄鋼や石油化学工場が集まる工業地帯は？|京浜工業地帯|けいひんこうぎょうちたい|京葉工業地域|けいようこうぎょうちいき|阪神工業地帯|はんしんこうぎょうちたい
14|三浦半島で、海に囲まれた温暖な冬を生かして出荷する代表的な根菜は？|だいこん|だいこん|ねぎ|ねぎ|キャベツ|きゃべつ
15|信濃川などの下流に、水はけを整えた水田が広がる平野は？|越後平野|えちごへいや|庄内平野|しょうないへいや|出雲平野|いずもへいや
15|金属製の食器や工具の地場産業で知られる、燕市と三条市周辺の呼び名は？|燕三条|つばめさんじょう|東濃|とうのう|西陣|にしじん
16|水田や屋敷林に囲まれた家が点在する散居村で知られる平野は？|砺波平野|となみへいや|庄内平野|しょうないへいや|讃岐平野|さぬきへいや
16|家庭に薬を預け、使った分の代金を受け取る売薬で知られる市は？|富山市|とやまし|鯖江市|さばえし|四日市市|よっかいちし
17|金沢で、金などを打ち延ばして薄い箔にする伝統工芸品は？|金沢箔|かなざわはく|南部鉄器|なんぶてっき|西陣織|にしじんおり
17|下流の扇状地に水田が広がり、加賀平野の用水に使われる川は？|手取川|てどりがわ|信濃川|しなのがわ|最上川|もがみがわ
18|福井県で、めがね枠を分業で作る地場産業で知られる市は？|鯖江市|さばえし|富山市|とやまし|多治見市|たじみし
18|福井県の港で水揚げされる雄のズワイガニの呼び名は？|越前がに|えちぜんがに|カツオ|かつお|ふぐ|ふぐ
19|勝沼周辺で育て、生食のほかワインにも加工する果物は？|ぶどう|ぶどう|りんご|りんご|みかん|みかん
19|笛吹市などが周辺にあり、水はけのよい土地に桃などの果樹園が広がる盆地は？|甲府盆地|こうふぼんち|福島盆地|ふくしまぼんち|山形盆地|やまがたぼんち
20|川上村の高原から、収穫後に冷やして夏に出荷する代表的な葉物野菜は？|レタス|れたす|ねぎ|ねぎ|小松菜|こまつな
20|長野県で、時計などの精密機械工業が発達した地域の中心にある湖は？|諏訪湖|すわこ|琵琶湖|びわこ|宍道湖|しんじこ
21|東濃の多治見・土岐などで作られてきた焼き物は？|美濃焼|みのやき|瀬戸焼|せとやき|有田焼|ありたやき
21|木材を加工する家具づくりがさかんな、岐阜県北部の地域は？|飛騨地方|ひだちほう|東濃地方|とうのうちほう|庄内地方|しょうないちほう
22|水はけのよい土地に茶畑が広がる、静岡県の台地は？|牧之原台地|まきのはらだいち|根釧台地|こんせんだいち|下総台地|しもうさだいち
22|静岡県の西部で、楽器やオートバイの工業が発達した市は？|浜松市|はままつし|豊田市|とよたし|四日市市|よっかいちし
23|愛知県で、自動車の組立工場や部品工場が多く集まる市は？|豊田市|とよたし|浜松市|はままつし|太田市|おおたし
23|愛知県の瀬戸市を中心に作られてきた焼き物は？|瀬戸焼|せとやき|美濃焼|みのやき|有田焼|ありたやき
24|志摩市にあり、入り江でアコヤガイを育てる真珠養殖がさかんな湾は？|英虞湾|あごわん|松島湾|まつしまわん|陸奥湾|むつわん
24|伊勢湾岸に石油化学工場が集まり、配管で工場同士がつながる市は？|四日市市|よっかいちし|浜松市|はままつし|豊田市|とよたし
25|湖東平野など、琵琶湖の周りに水田が広がる滋賀県で生産される米の総称は？|近江米|おうみまい|越後の米|えちごのこめ|秋田の米|あきたのこめ
25|海のない滋賀県で、ビワマスなどの漁業が行われる淡水の湖は？|琵琶湖|びわこ|宍道湖|しんじこ|諏訪湖|すわこ
26|京都府南部に産地があり、玉露や抹茶などでも知られる茶は？|宇治茶|うじちゃ|狭山茶|さやまちゃ|静岡茶|しずおかちゃ
26|京都で、先に染めた糸を織り合わせて帯などにする伝統工芸品は？|西陣織|にしじんおり|南部鉄器|なんぶてっき|金沢箔|かなざわはく
27|大阪・神戸を中心とし、堺の臨海部も含む工業地帯は？|阪神工業地帯|はんしんこうぎょうちたい|京浜工業地帯|けいひんこうぎょうちたい|中京工業地帯|ちゅうきょうこうぎょうちたい
27|金属を削ったり曲げたりする工程を、得意分野の異なる町工場が分担する大阪府の市は？|東大阪市|ひがしおおさかし|鯖江市|さばえし|豊田市|とよたし
28|兵庫県で、岸壁を利用して造船所が発達した港は？|神戸港|こうべこう|鹿島港|かしまこう|長崎港|ながさきこう
28|淡路島の南部で、米の収穫後の田を使って育てる代表的な野菜は？|たまねぎ|たまねぎ|キャベツ|きゃべつ|レタス|れたす
29|奈良県の吉野川上流で、建築材として長く育ててきた代表的な木は？|吉野杉|よしのすぎ|秋田杉|あきたすぎ|松|まつ
29|奈良県の五條市周辺で、日当たりのよい斜面の果樹園に育つ秋の果物は？|柿|かき|さくらんぼ|さくらんぼ|桃|もも
30|有田川流域の、日当たりと水はけのよい段々畑で育つ果物は？|みかん|みかん|ぶどう|ぶどう|りんご|りんご
30|みなべ・田辺で育て、塩漬けや天日干しにして保存食にする果実は？|梅|うめ|桃|もも|なし|なし
31|鳥取県の倉吉市などで栽培される「二十世紀」は何の果物？|なし（梨）|なし|桃|もも|りんご|りんご
31|鳥取市の福部地区で、水はけのよい砂丘地を利用して育てる作物は？|らっきょう|らっきょう|たまねぎ|たまねぎ|落花生|らっかせい
32|川の水と海水が混ざり、しじみ漁がさかんな島根県の湖は？|宍道湖|しんじこ|琵琶湖|びわこ|諏訪湖|すわこ
32|斐伊川の下流にあり、水田が広がる島根県の平野は？|出雲平野|いずもへいや|越後平野|えちごへいや|庄内平野|しょうないへいや
33|倉敷市にあり、製鉄・石油化学・自動車などの工場が周りに集まる港は？|水島港|みずしまこう|鹿島港|かしまこう|神戸港|こうべこう
33|岡山市周辺で、袋をかけて白い果皮に仕上げる桃は？|白桃|はくとう|びわ|びわ|なし|なし
34|広島市とその周辺で組み立てられ、完成品が港からも出荷される輸送機械は？|自動車|じどうしゃ|めがね枠|めがねわく|鉄瓶|てつびん
34|広島湾の波の穏やかな場所で、いかだからつるして育てる水産物は？|カキ|かき|わかめ|わかめ|のり|のり
35|山口県で、徳山湾岸に石油化学工場が集まる市は？|周南市|しゅうなんし|四日市市|よっかいちし|倉敷市|くらしきし
35|下関の南風泊市場に各地から集まり、取引される代表的な魚は？|ふぐ|ふぐ|カツオ|かつお|サバ|さば
36|神山町などで作られ、緑色の小さな実が料理に酸味を添えるかんきつは？|すだち|すだち|みかん|みかん|りんご|りんご
36|潮の流れを利用したわかめ養殖で知られ、徳島県と淡路島の間にある海峡は？|鳴門海峡|なるとかいきょう|関門海峡|かんもんかいきょう|津軽海峡|つがるかいきょう
37|香川県で、雨が少ない平野の水田に水を送るために使われてきた、まんのう町の大きな池は？|満濃池|まんのういけ|琵琶湖|びわこ|宍道湖|しんじこ
37|小麦粉をこねて麺にする、香川県の代表的な食べ物は？|讃岐うどん|さぬきうどん|ふなずし|ふなずし|水戸納豆|みとなっとう
38|八幡浜市周辺で日当たりのよい斜面を生かして育てる代表的なかんきつは？|みかん|みかん|すだち|すだち|ぶどう|ぶどう
38|愛媛県の瀬戸内海沿岸にあり、造船所が立ち並ぶ市は？|今治市|いまばりし|長崎市|ながさきし|神戸市|こうべし
39|安芸市周辺でハウスを使い、冬から春にも出荷する代表的な野菜は？|なす|なす|レタス|れたす|らっきょう|らっきょう
39|高知県の沖を流れ、カツオ漁と関わりが深い暖流は？|黒潮|くろしお|親潮|おやしお|リマン海流|りまんかいりゅう
40|筑豊の石炭や港の輸送を生かして明治時代に造られた官営の製鉄所は？|八幡製鉄所|やはたせいてつじょ|大分製鉄所|おおいたせいてつじょ|君津製鉄所|きみつせいてつじょ
40|福岡県の筑後地方で、ハウスで温度を調整して育てる代表的な赤い果実は？|いちご|いちご|梅|うめ|びわ|びわ
41|佐賀県の沿岸にあり、潮の満ち引きを利用したのり養殖がさかんな海は？|有明海|ありあけかい|宇和海|うわかい|オホーツク海|おほーつくかい
41|佐賀県で陶石を使って作り、伊万里の港からも運ばれた焼き物は？|有田焼|ありたやき|美濃焼|みのやき|瀬戸焼|せとやき
42|長崎市の茂木の温暖な斜面で育つ、大きな種がある橙色の果物は？|びわ|びわ|桃|もも|さくらんぼ|さくらんぼ
42|奥深い入り江を利用し、大型船を造って海へ出す施設が発達した長崎県の港は？|長崎港|ながさきこう|神戸港|こうべこう|鹿島港|かしまこう
43|熊本県で、野焼きなどで草原を手入れし、肉用牛を放牧する地域は？|阿蘇|あそ|根釧|こんせん|十勝|とかち
43|八代平野のハウスで育て、冬から春にも出荷される代表的な赤い実の野菜は？|トマト|とまと|いちご|いちご|ピーマン|ぴーまん
44|大分県の山あいで、クヌギの丸太に菌を植えて栽培するきのこは？|しいたけ|しいたけ|しめじ|しめじ|えのきたけ|えのきたけ
44|大分県の臨海部にあり、鉄鉱石を大型船で運べる製鉄所が面する湾は？|別府湾|べっぷわん|伊勢湾|いせわん|東京湾|とうきょうわん
45|宮崎平野で、冬の温暖な気候とハウスを利用し早く出荷する代表的な緑の野菜は？|ピーマン|ぴーまん|なす|なす|トマト|とまと
45|宮崎県の畜産で、卵をとるための鶏と区別し、肉用に育てる鶏の呼び名は？|ブロイラー|ぶろいらー|乳牛|にゅうぎゅう|肉牛|にくぎゅう
46|大隅半島などで育て、でんぷんや芋焼酎の原料にもなる作物は？|さつまいも|さつまいも|落花生|らっかせい|さとうきび|さとうきび
46|曽於市周辺などで育てられ、鹿児島県の代表的な豚として知られるのは？|黒豚|くろぶた|肉牛|にくぎゅう|ブロイラー|ぶろいらー
47|沖縄の暖かい気候を生かして育て、茎の汁から砂糖を作る作物は？|さとうきび|さとうきび|さつまいも|さつまいも|パイナップル|ぱいなっぷる
47|沖縄で海や歴史を目当てに来る旅行者に、宿泊や案内などを提供する産業は？|観光業|かんこうぎょう|造船業|ぞうせんぎょう|鉄鋼業|てっこうぎょう
"""

MAFF_REGIONAL_PROFILES = "https://www.maff.go.jp/j/kanbo/tiho/todouhuken_gaiyou2022.html"
FISH_STATISTICS = "https://www.jfa.maff.go.jp/j/kikaku/wpaper/r07_h/sankou/sankou_3_15.html"
MANUFACTURING_STATISTICS = "https://www.meti.go.jp/statistics/tyo/kkj/seizo_result.html"
CRAFT_PROFILES = "https://www.kanto.meti.go.jp/seisaku/chiiki_brand/index_densan.html"
TOPIC_SOURCES = {
    "01a": ("農林水産省｜十勝平野の農業", "https://www.maff.go.jp/j/nousin/sekkei/museum/m_siki/03_tokati/index.html"),
    "01b": ("TESTEA｜中学受験の北海道", "https://testea.net/chugaku-juken/tirihoxtukaidou/"),
    "04a": ("農林水産省｜大崎耕土", "https://www.maff.go.jp/j/nousin/kantai/giahs_3_092.html"),
    "07a": ("福島市｜桃・くだもの", "https://www.city.fukushima.fukushima.jp/kankounavi/contents/eat/11449.html"),
    "08c": ("農林水産省｜納豆", "https://www.maff.go.jp/j/keikaku/syokubunka/traditional-foods/menu/natto_ibaraki.html"),
    "12a": ("農林水産省｜千葉県の落花生", "https://www.maff.go.jp/j/keikaku/syokubunka/k_ryouri/search_menu/menu/yude_rakkasei_chiba.html"),
    "24a": ("志摩市｜真珠養殖", "https://www.city.shima.mie.jp/shisei/shi_no_shokai/shisei_yoran/1470808548377.html"),
    "25b": ("滋賀県｜琵琶湖の食文化・農水産物", "https://www.pref.shiga.lg.jp/biwako-system/18893.html"),
    "25c": ("滋賀県｜琵琶湖の食文化・農水産物", "https://www.pref.shiga.lg.jp/biwako-system/18893.html"),
    "30a": ("和歌山県｜有田みかんと石積みの段々畑", "https://www.pref.wakayama.lg.jp/prefg/000200/nagomi/w58/24/index.html"),
    "32a": ("島根県｜ヤマトシジミ", "https://www.pref.shimane.lg.jp/industry/suisan/shinkou/kawa_mizuumi/seibutu/yamatosi_jimi.html"),
    "13c": ("東京都｜都の統計", "https://www.toukei.metro.tokyo.lg.jp/"),
    "42a": ("長崎市｜長崎びわ", "https://www.city.nagasaki.lg.jp/page/2435.html"),
    "43a": ("農林水産省｜阿蘇の草原と農業", "https://www.maff.go.jp/j/nousin/kantai/giahs_3_040.html"),
}
TOPIC_ICONS = {
    "畑作":"root", "畑作・加工":"root", "稲作":"rice", "果樹":"fruit", "果樹・加工":"fruit",
    "茶":"tea", "畜産":"cow", "近郊農業":"leaf", "高原野菜":"leaf", "施設園芸":"greenhouse",
    "砂丘農業":"root", "農産物":"fruit", "漁業":"fish", "水産養殖":"shell",
    "内水面漁業":"fish", "水産流通":"fish",
}
EXAM_STORIES = {}
for row in EXAM_INDUSTRY_ROWS.strip().splitlines():
    pid, category, name, reading, locality, location, intro = row.split("|")
    stories = EXAM_STORIES.setdefault(pid, [])
    key = pid + chr(ord("a") + len(stories))
    if key in TOPIC_SOURCES:
        source_label, url = TOPIC_SOURCES[key]
    elif category in ("漁業", "水産養殖", "内水面漁業", "水産流通"):
        source_label, url = "水産庁｜都道府県別の漁業・養殖業", FISH_STATISTICS
    elif category in ("伝統工芸", "窯業"):
        source_label, url = "経済産業省｜伝統的工芸品", CRAFT_PROFILES
    elif "工業" in category:
        source_label, url = "経済産業省｜製造業の地域別統計", MANUFACTURING_STATISTICS
    elif category == "サービス業":
        source_label, url = "観光庁｜観光統計", "https://www.mlit.go.jp/kankocho/siryou/toukei/index.html"
    else:
        source_label, url = "農林水産省｜都道府県の農林水産業", MAFF_REGIONAL_PROFILES
    story = dict(key=key, name=name, reading=reading, category=category, intro=intro, source=url,
                 source_label=source_label, place={"label": locality, "point": project(pid, location)},
                 icon=TOPIC_ICONS.get(category))
    stories.append(story)


EXAM_QUESTIONS = {}
for row in EXAM_NAME_ROWS.strip().splitlines():
    pid, prompt, answer, reading, wrong1, reading1, wrong2, reading2 = row.split("|")
    questions = EXAM_QUESTIONS.setdefault(pid, [])
    index = len(questions)
    options = [(answer, reading), (wrong1, reading1), (wrong2, reading2)]
    labels = [name if "（" in name or re.fullmatch(r"[ぁ-ヿー]+", name)
              else f"{name}（{kana}）" for name, kana in options]
    skill = "map" if answer.endswith(("平野", "台地", "海岸", "浜", "湾", "川", "盆地",
                                       "湖", "地方", "海峡", "池", "海", "潮")) else "industry"
    questions.append(dict(
        id=f"geography.discovery.{pid}.name.{index + 1}", prompt=prompt,
        options=labels, readings=[kana for _, kana in options], correct="0", skill=skill,
        explanation=EXAM_STORIES[pid][index]["intro"],
    ))


# These prefectures' previous quiz answers named places. Ask about the product or work described in the study card.
INDUSTRY_QUIZ_QUESTIONS = {
    "01": (1, "根釧台地で、乳牛を育てて牛乳を作る仕事は？",
           ("酪農", "らくのう"), ("稲作", "いなさく"), ("造船業", "ぞうせんぎょう")),
    "04": (1, "宮城県の松島湾で、海につるして育てる貝は？",
           ("カキ", "かき"), ("シジミ", "しじみ"), ("アワビ", "あわび")),
    "16": (1, "富山市の売薬の伝統とつながりが深い工業は？",
           ("医薬品工業", "いやくひんこうぎょう"), ("造船業", "ぞうせんぎょう"), ("製鉄業", "せいてつぎょう")),
    "22": (0, "静岡県の牧之原台地で、葉を摘み取って加工する作物は？",
           ("茶", "ちゃ"), ("みかん", "みかん"), ("メロン", "めろん")),
    "24": (0, "三重県の英虞湾で、アコヤガイを育てて作るものは？",
           ("真珠", "しんじゅ"), ("干しのり", "ほしのり"), ("かつお節", "かつおぶし")),
    "32": (0, "島根県の宍道湖でとれる、川の水と海水が混ざる場所にすむ貝は？",
           ("ヤマトシジミ", "やまとしじみ"), ("アコヤガイ", "あこやがい"), ("ホタテガイ", "ほたてがい")),
}


def prefecture_prompt(name, prompt):
    if name == "東京都":
        prompt = prompt.replace("東京都心", "東京都の都心")
    return prompt if name in prompt else f"{name}について、{prompt}"


def prefecture_quiz(pid):
    info = PREFECTURE_INFO[pid]
    name = info["name"]
    region = region_of(pid)[0]
    others = sorted((other for other in PREFECTURE_INFO if other != pid),
                    key=lambda other: (region_of(other)[0] != region, abs(int(other) - int(pid))))

    def fact_question(field, skill, prompt, explanation):
        answer = info[field]
        choices = {answer: info[f"{field}_reading"]}
        for other in others:
            entry = PREFECTURE_INFO[other]
            choices.setdefault(entry[field], entry[f"{field}_reading"])
            if len(choices) == 3:
                break
        return dict(id=f"geography.discovery.{pid}.quiz3.{field}", prompt=prompt,
                    options=[f"{name}（{reading}）" for name, reading in choices.items()],
                    readings=list(choices.values()), correct="0", skill=skill, explanation=explanation)

    office = f"{name[-1]}庁所在地"
    capital = fact_question("capital", "capital", f"{name}の{office}はどこ？",
                            f"{name}の{office}は{info['capital']}です。")
    terrain = fact_question("land", "map", f"地図でたしかめた{name}の主な地形の名前は？",
                            f"{info['land']}は、この地図で学んだ{info['kind']}です。")
    if pid in INDUSTRY_QUIZ_QUESTIONS:
        story_index, prompt, *options = INDUSTRY_QUIZ_QUESTIONS[pid]
        industry = dict(prompt=prompt, options=[name if name == kana else f"{name}（{kana}）" for name, kana in options],
                        readings=[kana for _, kana in options], correct="0", skill="industry",
                        explanation=EXAM_STORIES[pid][story_index]["intro"])
    else:
        industry = next(q for q in EXAM_QUESTIONS[pid]
                        if q["skill"] == "industry"
                        and not q["options"][0].split("（", 1)[0].endswith(("市", "町", "村", "港"))
                        and q["options"][0].split("（", 1)[0] != "阿蘇")
    industry = {**industry, "id": f"geography.discovery.{pid}.quiz3.industry",
                "prompt": prefecture_prompt(name, industry["prompt"])}
    return [capital, terrain, industry]


DISCOVERY = {
    pid: {**{key: info[key] for key in ("name", "reading", "capital", "capital_reading", "land", "land_reading", "kind", "climate")},
          "capital_point": project(pid, CAPITAL_POINTS[pid]),
          "land_point": project(pid, info["place"]), "questions": prefecture_quiz(pid),
          "previous_questions": [
              {**q, "prompt": prefecture_prompt(info["name"], q["prompt"])} for q in EXAM_QUESTIONS[pid]
          ],
          "industry_stories": EXAM_STORIES[pid], "seas": SEA_LABELS.get(pid, []),
          "land_overlay": LAND_OVERLAYS.get(pid),
          "core_rivers": [feature["name"] for feature in VERIFIED_MAP[pid]["rivers"]
                          if feature["name"] in CORE_RIVERS or feature["name"] == info["land"]],
          "core_peaks": [feature["name"] for feature in VERIFIED_MAP[pid]["peaks"]
                         if re.split("[（＜]", feature["name"])[0] in CORE_PEAKS
                         or feature["name"].startswith(info["land"])],
          "land_neighbors": LAND_NEIGHBORS.get(pid, []),
          "sea_neighbors": SEA_NEIGHBORS.get(pid, []), **VERIFIED_MAP[pid]}
    for pid, info in PREFECTURE_INFO.items()
}


def catalog():
    def entry(kind, ident, payload):
        return dict(schema_version=1, source_app=SOURCE, content_version=VERSION,
                    entry_type=kind, entry_id=ident, payload=payload)
    for key, name in SKILLS.items():
        ident = f"geography.discovery.{key}"
        yield entry("skill", ident, dict(skill_id=ident, label=name))
    for ident, menu in MENUS.items():
        yield entry("menu", ident, menu)
    for pid, info in DISCOVERY.items():
        for q in info["questions"]:
            yield entry("question", q["id"], dict(
                question_id=q["id"], prompt=q["prompt"], label=q["prompt"], skill_ids=[f"geography.discovery.{q['skill']}"],
                question_family_id=f"geography.discovery.{q['skill']}", prefecture_id=pid,
                menu_ids=[key for key, menu in MENUS.items() if pid in menu["prefectures"]],
                assessment_method="automatic", correct_option_id=q["correct"]))


def build_records(raw, profile, assignment=None, now=None):
    if raw.get("menu") in LEGACY_MENUS:
        return build_legacy_records(raw, profile, assignment, now)
    attempt = UUID(raw["id"])
    content_version = raw.get("content_version", PREVIOUS_VERSION)
    if content_version == VERSION:
        menu = MENUS[raw["menu"]]
    elif content_version == PREVIOUS_VERSION:
        menu = PREVIOUS_MENUS[raw["menu"]]
    elif content_version in (TWO_QUESTION_VERSION, DESCRIPTIVE_VERSION, ARCHIVE_VERSION):
        menu = TWO_QUESTION_MENUS[raw["menu"]]
    else:
        raise ValueError("unknown quiz version")
    pid = raw["pref"]
    status = raw["status"]
    lo, hi = parse(raw["started"]), parse(raw["ended"])
    total = menu["planned_question_count"]
    items = raw["questions"]
    if (attempt.version != 4 or pid not in menu["prefectures"] or status not in ("completed", "abandoned")
            or not isinstance(items, list) or len(items) > total or lo > hi
            or hi > (now or datetime.now(timezone.utc)) + timedelta(minutes=5)):
        raise ValueError("invalid attempt")
    events = []

    def add(kind, when, payload, question=None, occurrence=None, segment=None):
        events.append((when, kind, payload, question, occurrence, segment))

    start = dict(menu_id=menu["menu_id"], category_id=menu["category_id"], difficulty_id=menu["difficulty_id"],
                 planned_question_count=total, mode="challenge", prefecture_id=pid,
                 settings_snapshot={"activity": "prefecture_discovery", "question_count": total, "explored_before_quiz": True})
    if (assignment and raw.get("assignment") == assignment["plan_item_id"]
            and menu["menu_id"] == assignment["menu_id"] and assignment["content_version"] == content_version):
        start["plan_item_id"] = assignment["plan_item_id"]
    add("session_started", lo, start)
    opened = set()
    placed = False
    previous = lo
    actions = raw["actions"]
    if not isinstance(actions, list) or len(actions) > 200:
        raise ValueError("invalid map activity")
    for action in actions:
        at = parse(action["at"])
        if not previous <= at <= hi:
            raise ValueError("invalid action time")
        previous = at
        kind = action["type"]
        data = {"prefecture_id": pid}
        if kind == "placement" and not placed:
            target = action.get("target")
            if target is not None and target not in PREFECTURES:
                raise ValueError("invalid drop")
            placed = target == pid
            add("learning_activity", at, {**data, "activity": "map_placement",
                "selected_prefecture_id": target, "is_correct": placed})
        elif kind == "hint" and not placed:
            add("support_used", at, {**data, "support_type": "hint", "hint_step": 1})
        elif kind == "zoom" and not placed:
            add("learning_activity", at, {**data, "activity": "map_zoom"})
        elif kind == "explore" and placed and action.get("feature") in ("capital", "land", "industry"):
            feature = action["feature"]
            if feature not in opened:
                opened.add(feature)
                add("learning_activity", at, {**data, "activity": "prefecture_feature_opened", "feature": feature})
        else:
            raise ValueError("invalid activity")
    if items and (not placed or (content_version != ARCHIVE_VERSION and not {"capital", "land", "industry"} <= opened)):
        raise ValueError("exploration missing")

    correct = answered = 0
    if content_version == PREVIOUS_VERSION:
        sources = previous_discovery_questions(pid)
    elif content_version == ARCHIVE_VERSION:
        sources = [dict(id=ident, correct="0", skill=skill)
                   for ident, skill in zip(ARCHIVE_QUESTIONS_V3[pid], ARCHIVE_QUESTION_SKILLS, strict=True)]
    elif content_version == DESCRIPTIVE_VERSION:
        sources = [dict(id=f"geography.discovery.{pid}.exam.{index}", correct="0", skill=skill)
                   for index, skill in enumerate(("industry", "reasoning"), 1)]
    elif content_version == TWO_QUESTION_VERSION:
        sources = EXAM_QUESTIONS[pid]
    else:
        sources = DISCOVERY[pid]["questions"]
    for index, item in enumerate(items):
        question = sources[index]
        at = parse(item["shown"])
        options = item["options"]
        if (not previous <= at <= hi or item["id"] != question["id"]
                or not isinstance(options, list) or len(options) != 3 or set(options) != {"0", "1", "2"}):
            raise ValueError("invalid question")
        occur = str(uuid5(attempt, question["id"]))
        add("item_presented", at, dict(presentation_kind="first", parent_occurrence_id=None, order=index+1,
            answer_exposed_before=question["id"].rsplit(".", 1)[-1] != "evidence",
            choice_order=options), question["id"], occur)
        choice = item.get("choice")
        previous = at
        if choice is None:
            if status == "completed" or index != len(items)-1:
                raise ValueError("incomplete question")
            continue
        when = parse(item["answered"])
        if choice not in options or not at <= when <= hi:
            raise ValueError("invalid answer")
        method = item.get("input_method", "choice")
        if method not in ("choice", "speech"):
            raise ValueError("invalid answer input method")
        previous = when
        right = choice == question["correct"]
        correct += int(right)
        answered += 1
        add("response_submitted", when, dict(response_index=1, response_status="answered",
            assessment_method="automatic", is_correct=right, input_method=method,
            response_value={"choice_id": choice, "prefecture_id": pid, "skill": question["skill"]},
            support_before_response={"hint_count": 0, "explanation_seen": False, "answer_seen": False,
                "worked_example_seen": False, "parent_help": False},
            answer_latency_ms=int((when-at).total_seconds()*1000)), question["id"], occur)
    if status == "completed" and answered != total:
        raise ValueError("invalid completion")

    previous = lo
    intervals = raw["intervals"]
    if not isinstance(intervals, list) or len(intervals) > 500:
        raise ValueError("invalid intervals")
    for index, pair in enumerate(intervals):
        a, b = map(parse, pair)
        duration = round((b-a).total_seconds()*1000)
        if not previous <= a < b <= hi or duration > 180_000:
            raise ValueError("invalid interval")
        previous = b
        add("time_interval_closed", b, dict(start_at=iso(a), end_at=iso(b), active_ms=duration,
            timing_quality="complete", phase="other"), segment=str(uuid5(attempt, f"interval:{index}")))
    add("session_ended", hi, dict(status=status, answered_count=answered, first_correct_count=correct, prefecture_id=pid))
    records = []
    for sequence, (when, kind, payload, question, occurrence, segment) in enumerate(
            sorted(events, key=lambda e:e[0]), 1):
        event = dict(schema_version=1, source_app=SOURCE, profile_id=profile, attempt_id=str(attempt),
            event_id=str(uuid5(attempt, f"event:{sequence}")),
            app_version={PREVIOUS_VERSION:"2.0.0", ARCHIVE_VERSION:"3.0.0",
                         DESCRIPTIVE_VERSION:"4.0.0", TWO_QUESTION_VERSION:"5.0.0",
                         VERSION:"6.0.0"}[content_version],
            content_version=content_version,
            event_type=kind, occurred_at=iso(when), sequence=sequence, question_id=question,
            occurrence_id=occurrence, segment_id=segment, payload=payload)
        event["event_hash"] = hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode()).hexdigest()
        records.append(event)
    medal = None if status != "completed" else dict(
        source_app=SOURCE, profile_id=profile, attempt_id=str(attempt), category_key=menu["category_id"],
        category_label=PREFECTURES[pid]["name"]+"の発見", stamp_char="地", reading="ち", difficulty=menu["difficulty_id"],
        correct_count=correct, total_count=total, grade="gold" if correct == total else "silver", finished_at=iso(hi))
    return records, medal


# Streamlitのカスタムコンポーネント。配布時の追加ファイルは不要。
FRONTEND_HTML = r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>日本地図パズル</title>
<style>
:root{color-scheme:light;--ink:#153d3a;--muted:#49645e;--paper:#f8f8ea;--panel:#fffef5;--edge:#bfd3c6;--dark:#12624b;--sea:#d9efef;--piece:#ffc870;--win:#83c6a2;font:16px/1.55 "Hiragino Sans","Noto Sans CJK JP",system-ui,sans-serif;color:var(--ink)}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:var(--paper);padding:clamp(12px,3vw,32px);border-radius:22px}
header{display:grid;justify-items:start;gap:12px;padding-bottom:12px;border-bottom:1px solid var(--edge)}
header{grid-template-columns:1fr auto}
@media(max-width:540px){header{grid-template-columns:1fr}}
.subject{font-size:.85rem;color:var(--dark);font-weight:750;letter-spacing:.08em}
h1{font-size:clamp(1.65rem,5vw,2.6rem);letter-spacing:.035em;line-height:1.2;margin:5px 0 0}
h2{margin:0 0 12px;font-size:1.25rem}
a{color:var(--dark)}
button{min-height:42px;border:1px solid var(--dark);background:var(--dark);color:white;border-radius:11px;padding:7px 13px;font:inherit;font-weight:700;cursor:pointer}
button:focus-visible,#map:focus-visible,a:focus-visible{outline:3px solid #a76400;outline-offset:3px}
button:disabled{cursor:default}
.secondary{background:var(--panel);color:var(--dark);border-color:var(--edge)}
.sync{display:flex;align-items:center;gap:8px;min-height:36px;color:var(--muted);font-size:.79rem}
.sync button{font-size:inherit;min-height:32px;padding:4px 9px;background:var(--panel);color:var(--dark);border-color:var(--edge)}
#courses{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(190px,100%),1fr));gap:10px;margin-bottom:16px}
#courses button{text-align:left;background:var(--panel);color:var(--ink);border-color:var(--edge);min-height:66px}
#assigned-course button{background:#e5f2e9;color:var(--ink);text-align:left}
#assigned-course small{display:block;color:var(--muted);font-weight:500}
#courses small{display:block;color:var(--muted);font-weight:500}
.progress,.actions{display:flex;justify-content:space-between;gap:12px;align-items:center}
.instruction{font-weight:750;margin:10px 0 6px}
.play{display:grid;grid-template-columns:145px minmax(0,1fr);gap:12px}
.tray{display:flex;flex-direction:column;gap:7px}
.map-controls{display:flex;flex-direction:column;gap:7px}
#piece{display:grid;width:100%;justify-items:center;background:#fff3d7;border-color:#ae6a21;color:#653d15;touch-action:none;user-select:none;cursor:grab}
#piece[aria-pressed=true]{background:#ffdf9e}
#piece:disabled{opacity:.6}
#pieceImage{display:block;width:100%;height:96px;overflow:visible;pointer-events:none}
#resume,#assigned-course{margin:0 0 10px}
.region-heading{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:9px}
.region-heading h2{margin:0 0 12px}
#board-label{font-weight:750;font-size:.85rem;color:var(--muted)}
#placement-recall{display:flex;align-items:center;flex-wrap:wrap;gap:8px 12px;margin:6px 0 10px}
#placement-recall h2{margin:0;font-size:clamp(1.1rem,3vw,1.45rem)}
#placement-map.is-placed{grid-template-columns:1fr}
#placement-map.is-placed #map{cursor:default}
#placement-map.is-placed #inset text{display:none}
.menu-extra{display:flex;gap:8px;flex-wrap:wrap}
#courses button{text-align:left}

#piecePath,#ghost{stroke-linejoin:round;vector-effect:non-scaling-stroke}
#ghost{fill:var(--piece);stroke:#824712;stroke-width:1.25}
.map-frame{background:var(--sea);border:1px solid #98c3c5;border-radius:13px;display:grid;place-items:center;overflow:hidden}
#map{width:100%;display:block;max-height:520px;cursor:crosshair;user-select:none}
#outlines path{fill:#f6edcf;stroke:#547770;stroke-width:.7;stroke-linejoin:round;vector-effect:non-scaling-stroke}
#outlines path:nth-child(2n){fill:#f3e5bc}
#outlines path.found{fill:var(--win);stroke:#184d37;stroke-width:1.6}
#outlines path.hinted{fill:#fad590;stroke:#a45f1c;stroke-width:2.2}
#outlines path.keyboard{stroke:#103d69;stroke-width:3}
#inset rect{stroke:#73969a;stroke-dasharray:4 3;fill:#cce5e5}
#inset text{fill:#315459;font-weight:700;font-size:12px}
#feedback{color:#264f45;margin:8px 0}
#choices{display:grid;grid-template-columns:1fr;gap:6px;margin:8px 0;padding:0;list-style:none}
#choices li{background:var(--panel);color:var(--ink);border:1px solid var(--edge);
  border-radius:8px;padding:6px 10px;overflow-wrap:anywhere}
#choices .answer{border-color:var(--dark);background:#dcf0e0}
#choices .incorrect{border-color:#a9442e;background:#fce8dd}
#quiz-voice{margin:10px 0}
#quiz-format,#quiz-voice-status{margin:4px 0;color:var(--muted);font-size:.9rem}
#quiz-voice-status:empty{display:none}
footer{margin-top:13px;padding-top:8px;border-top:1px solid var(--edge);font-size:.72rem;color:var(--muted)}
@media(max-width:540px){
 .play{grid-template-columns:1fr;gap:5px}
 .tray{flex-direction:row;align-items:center}
 #piece{width:auto;grid-template-columns:70px 1fr;align-items:center;padding:2px 6px;font-size:.74rem;white-space:nowrap}
 #pieceImage{height:58px}
 .map-controls{flex-direction:row;margin-left:auto;gap:4px}
 .map-controls button{min-height:40px;padding:4px;font-size:.72rem}
}
#age-label{display:block;margin:0 0 14px;color:var(--muted)}
#age{font:inherit;border:1px solid var(--edge);border-radius:8px;padding:6px;color:var(--ink);background:var(--panel)}
#phase-explore,#phase-quiz{margin-top:12px}
#pref-name,#quiz-prompt{margin:0 0 5px;font-size:clamp(1.2rem,3vw,1.7rem)}
#pref-capital,#quiz-name{margin:0 0 6px;color:var(--muted);font-weight:700}
.voice-tools{display:flex;flex-wrap:wrap;gap:6px;justify-content:flex-end}
.voice-tools label{display:inline-flex;align-items:center;gap:7px;min-height:44px;color:var(--muted);font-size:.85rem;cursor:pointer}
.voice-tools input{width:18px;height:18px;accent-color:var(--dark)}
.discovery-map{background:linear-gradient(#d0ecea,#e4f4f0);border:1px solid #94bcbb;border-radius:13px;overflow:hidden}
#phase-explore{--explanation-accent:#8b4e23}
#fact-map{display:block;width:100%;height:auto;max-height:428px}
.neighbor-shape{fill:#f3f4e8;stroke:#9ab8ae;stroke-width:.85;vector-effect:non-scaling-stroke}
.neighbor-name{font-size:16px;font-weight:600;fill:#6a8077;paint-order:stroke;
  stroke:#f8fbef;stroke-width:3;stroke-linejoin:round}
#fact-neighbors,#fact-neighbor-names{pointer-events:none}
#nearby-prefectures{margin:5px 0 2px;color:#365e54;font-size:.78rem}
#nearby-prefectures span{display:inline-block;margin-right:.85em}
#fact-shape{fill:#e8eed8;stroke:#427266;stroke-width:1.3;vector-effect:non-scaling-stroke}
.capital-point circle{fill:#fffdf3;stroke:#496358;stroke-width:1.3}
.capital-point text{fill:#254f43}
.capital-point .capital-name{fill:var(--explanation-accent);font-size:19px;font-weight:850;paint-order:stroke;stroke:#fffef4;stroke-width:3.5;stroke-linejoin:round}
.sea-name{fill:#607e85;font-size:15px;font-weight:650;paint-order:stroke;stroke:#dff4f3;stroke-width:3;pointer-events:none}
.sea-name.bay-name{font-size:12px}
.industry-shortcuts{display:grid;gap:5px}
#fact-land-extent{pointer-events:none;stroke-width:1.4;stroke-linejoin:round;stroke-linecap:round;
  vector-effect:non-scaling-stroke}
#fact-land-extent.land-area{fill:#f4b65b;fill-opacity:.62;stroke:#a66629}
#fact-land-extent.land-water{fill:#efa04b;fill-opacity:.88;stroke:#974d20;stroke-width:2}
#fact-land-extent.land-coast{fill:none;stroke:#a66629;stroke-width:4}
#fact-land-extent.map-river{stroke:#2d77ab;stroke-width:2.15}
#fact-land-extent.map-river.selected{stroke:#024774;stroke-width:3.65}
.place-reference.primary-land{font-size:17px;font-weight:850;fill:var(--explanation-accent)}
#fact-title,#industry-name{color:var(--explanation-accent)}
.place-reference.secondary-land{fill:#587970}
#fact-map-panel.has-industry-shortcuts{display:grid;grid-template-columns:minmax(0,1fr) clamp(176px,31%,300px);
  gap:3px;align-items:start}
#fact-map-panel.has-industry-shortcuts #fact-map{max-height:none}
#map-industry-shortcuts{padding:5px;grid-template-columns:repeat(2,minmax(0,1fr));align-content:start}
#map-industry-shortcuts button[aria-pressed=true]{background:#fff4de;border-color:#a15a29;color:var(--ink)}
#map-industry-shortcuts button{display:block;width:100%;min-height:44px;padding:6px;border:1px solid var(--edge);
  background:transparent;color:var(--ink);border-radius:4px;text-align:left}
@media(max-width:540px){
  #fact-map-panel.has-industry-shortcuts{grid-template-columns:minmax(0,1fr)}
  #map-industry-shortcuts{grid-template-columns:repeat(auto-fit,minmax(min(84px,100%),1fr))}
}
.map-production-region{fill:#eab971;fill-opacity:.20;stroke:#a67747;stroke-width:1}
.map-production-region.active{fill:#f2a346;fill-opacity:.75;stroke:#8e481b;stroke-width:1.9}
.production-marker text{fill:#70421c;font-weight:800;pointer-events:none}
.production-marker{cursor:pointer}
.production-marker circle{fill:#fffef4;stroke:#9b632d;stroke-width:1.15}
.map-leader{stroke:#776650;stroke-width:1.5;pointer-events:none;vector-effect:non-scaling-stroke}
.map-leader-dot{fill:#776650;pointer-events:none}
.terrain-context #fact-land-extent.land-area,.terrain-context #fact-land-extent.land-water{fill:#93bc99;fill-opacity:.56;stroke:#567c62}
.terrain-context #fact-land-extent.land-coast{stroke:#567c62}
.terrain-context .place-reference{fill:#285844}
.terrain-context .place-reference.river-name{fill:#174f79}
.terrain-context .place-reference.peak-name{fill:#34584a}
.production-marker.active circle{fill:#f9d08d;stroke:#8d461c;stroke-width:2}
.map-peak[role=button],.river-hit{cursor:pointer}
.map-river{fill:none;stroke:#2d77ab;stroke-width:2.15;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.map-river.selected{stroke:#024774;stroke-width:3.65}
.river-hit{fill:none;stroke:transparent;stroke-width:16;pointer-events:stroke;vector-effect:non-scaling-stroke}
.map-peak circle{fill:#fff9ec;stroke:none;opacity:.82}
.map-peak .peak-back{fill:#77958c;stroke:#355b53;stroke-width:.8}
.map-peak .peak-front{fill:#427d65;stroke:#264f40;stroke-width:1;stroke-linejoin:round}
.map-peak .peak-snow{fill:#fffdf4}
.map-peak.selected circle{fill:#f2d4a7;stroke:#785b36;stroke-width:1.5}
#fact-map [tabindex]:focus-visible{outline:2px solid #aa6522;outline-offset:2px}
#relief-controls{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
#relief-controls button{font-size:.83rem;min-height:38px}
#relief-controls .relief-river{color:#155982}
#relief-controls .relief-peak{color:#674371}
#relief-controls button[aria-pressed=true]{background:#e7f0eb;border-color:#617c71}
.industry-icon{fill:none;stroke:#504333;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.map-key{display:flex;flex-wrap:wrap;gap:6px 15px;margin:8px 0 2px;color:#2b5147;font-size:.83rem}
.map-key span{display:inline-flex;gap:6px;align-items:center}
.map-key svg{width:21px;height:21px}
.map-note{margin:0;color:var(--muted);font-size:.73rem}
 .place-reference{font-size:12px;font-weight:750;fill:#386252;paint-order:stroke;stroke:#fbfff4;stroke-width:3;pointer-events:none}
#medal-dialog{width:min(360px,calc(100% - 30px));padding:18px;border:1px solid var(--edge);border-radius:19px;background:#fffef6;color:var(--ink);text-align:center;box-shadow:0 12px 40px #18362e45}
#medal-dialog::backdrop{background:#18362e78}
body:has(#medal-dialog[open]){min-height:365px}
.medal-stamp{box-sizing:border-box;display:grid;place-content:center;gap:0;width:106px;height:106px;margin:8px auto;border:5px double;border-radius:50%;line-height:1.12;box-shadow:inset 0 6px 13px #ffffffa1,0 6px 14px #10283022}
.medal-stamp.gold{background:radial-gradient(circle at 28% 18%,#fff9cf,#f5d361 49%,#c38d1d);border-color:#bd8c26;color:#69470a}
.medal-stamp.silver{background:radial-gradient(circle at 28% 18%,#fff,#d8e0e8 53%,#9aa8b8);border-color:#9aa9b8;color:#3d5266}
.medal-stamp b{font-size:37px}
#medal-status,#result-sync{color:var(--muted);font-size:.85rem}
.feature-keys{display:flex;flex-wrap:wrap;gap:6px;padding:8px 0}
.feature-keys button[aria-pressed=true]{background:#e5f2e9;border-color:var(--dark)}
.fact,#quiz-feedback{background:#fffef5;border:1px solid var(--edge);padding:9px 13px;margin:4px 0 12px;border-radius:11px}
#industry-stories{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(230px,100%),1fr));gap:8px;margin-top:10px}
#relief-list-title{margin-top:8px;font-weight:700}
.local-story{padding:9px 11px;background:#edf5e9;border-radius:9px}
.local-story.active{background:#fff4de;box-shadow:inset 0 0 0 2px #a15a29}
.local-story h4{margin:0;color:#214f41;font-size:1.05rem}
.local-story .story-pick{min-height:0;padding:2px 0;border:0;background:none;color:inherit;
  font:inherit;text-align:left;text-decoration:underline;text-underline-offset:3px}
.local-story .story-pick:hover{color:var(--explanation-accent)}
.local-story p{margin:4px 0}
.local-story .story-category,#pref-capital.supplement,
  #map-caption,#nearby-prefectures,.map-key{color:#526f66;font-size:.82rem}
#map-caption:empty{display:none}
.local-story a{display:inline-block;padding:3px 0;color:#47685e;font-size:.82rem}
.fact h3,.fact p{margin:0 0 6px}
#start-quiz:disabled{opacity:.5}
.actions{margin-top:14px}
</style>
<style>.cm-graduation-badge{display:inline-block;color:#a12e61;font-weight:800;margin:.2rem .4rem}
.cm-graduation-complete:disabled{color:#5b3c4b!important;opacity:.9!important;cursor:default}
</style></head>
<body>
<header>
  <div><div class="subject">ちょこまな　しゃかい・ちり</div><h1>日本地図パズル</h1></div>
  <div class="voice-tools">
    <label><input type="checkbox" id="voice-toggle" checked><span id="voice-label">自動読み上げ</span></label>
  </div>
</header>
<div class="sync"><output id="connection">学習記録を準備中…</output><button id="retry" hidden>再接続・同期</button></div>
<main>
  <section id="menu" hidden>
    <div class="region-heading">
      <h2 id="region-heading" tabindex="-1">どの地方から はじめる？</h2>
      <label id="age-label" for="age">ねんれい <select id="age"></select></label>
    </div>
    <button id="resume" class="secondary" hidden>つづきから</button>
    <div id="assigned-course" hidden></div>
    <div id="courses"></div>
    <div class="menu-extra">
      <button id="national-course" class="secondary" hidden>全国から 出題</button>
      <button id="export" class="secondary">UI・通信ログを保存</button>
    </div>
  </section>
  <section id="game" hidden>
    <div class="progress"><strong id="course"></strong><span id="count" aria-live="polite"></span></div>
    <div id="phase-map">
    <p class="instruction" id="prompt">ピースを 地図の ぴったりの場所へ <span id="board-label"></span></p>
    <div id="placement-recall" hidden>
      <h2 id="recall-prompt" tabindex="-1">ぴったり！ どの都道府県かな？</h2>
      <button type="button" id="reveal-prefecture">名前を たしかめる</button>
    </div>
    <div id="placement-map" class="play">
      <div id="placement-tray" class="tray">
        <button type="button" id="piece" aria-label="ピースをつかむ" aria-pressed="false">
          <svg id="pieceImage" viewBox="0 0 120 90" aria-hidden="true" focusable="false">
            <g id="pieceLayer">
              <path id="piecePath" fill="#f4a742" stroke="#703a14" stroke-width="2" vector-effect="non-scaling-stroke" fill-rule="evenodd"/>
            </g>
          </svg>
          <span>ピースを つかむ</span>
        </button>
        <div class="map-controls"><button id="zoom" class="secondary">ちいきを 拡大</button><button id="hint" class="secondary">ヒント</button></div>
      </div>
      <div class="map-frame">
        <svg id="map" viewBox="0 0 755 635" role="group" aria-label="日本地図。地図にピースをはめる。矢印キーで候補を移動し、Enterでおく。" tabindex="0">
          <g id="inset"><rect x="510" y="416" width="230" height="162" rx="12"/><text x="524" y="439">おきなわ（拡大）</text></g>
          <g id="outlines"></g>
          <path id="ghost" fill-rule="evenodd" pointer-events="none" visibility="hidden"/>
        </svg>
      </div>
    </div>
    <p id="feedback" role="status" aria-live="polite">ドラッグするか、ピースと置く場所を順にタップ。</p>
    </div>
    <div id="phase-explore" hidden>
      <h2 id="pref-name" tabindex="-1"></h2>
      <p id="pref-capital"></p>
      <div id="fact-map-panel" class="discovery-map">
        <svg id="fact-map" viewBox="0 0 560 330" role="group" aria-label="都道府県と周辺の地図。県庁、地形、産業・特産品のしるし。">
          <defs>
            <clipPath id="fact-clip"><use href="#fact-shape"/></clipPath>
          </defs>
          <g id="fact-neighbors" aria-hidden="true"></g>
          <path id="fact-shape" fill-rule="evenodd" clip-rule="evenodd"/>
          <g id="fact-land-clip" aria-hidden="true"><path id="fact-land-extent" hidden/></g>
          <g id="fact-neighbor-names" aria-hidden="true"></g>
          <g id="fact-water" aria-hidden="true"></g>

          <g id="fact-product-regions" clip-path="url(#fact-clip)" aria-hidden="true"></g>
          <g id="fact-rivers" clip-path="url(#fact-clip)"></g>
          <g id="fact-peaks"></g>
          <g id="fact-leaders" aria-hidden="true"></g>
          <g id="fact-terrain-labels" aria-hidden="true"></g>
          <g id="fact-pins"></g>
        </svg>
        <div id="map-industry-shortcuts" class="industry-shortcuts" role="group" aria-label="地図で見る産業・特産品を選ぶ" hidden></div>
      </div>
      <div class="map-key">
        <span id="capital-key-group" hidden>★ 県庁所在地</span>
        <span id="terrain-key-group" hidden>川・山と地形</span>
        <span id="industry-key-group" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><g id="industry-key-symbol" class="industry-icon"></g></svg><span id="industry-name"></span></span>
      </div>
      <p class="map-note" id="map-caption"></p>
      <p id="nearby-prefectures" hidden><span id="land-neighbor-list"></span><span id="sea-neighbor-list"></span></p>
      <p id="relief-list-title" class="map-note" hidden>地形の一覧</p>
      <div id="relief-controls" role="group" hidden aria-labelledby="relief-list-title"></div>
      <div class="feature-keys">
        <button id="discover-capital" aria-pressed="false" class="secondary">★ 県庁 <span hidden>✓</span></button>
        <button id="discover-land" aria-pressed="false" class="secondary">● 地形 <span hidden>✓</span></button>
        <button id="discover-industry" aria-pressed="false" class="secondary">産業・特産品 <span hidden>✓</span></button>
      </div>
      <article id="explore-fact" class="fact" aria-live="polite">
        <h3 id="fact-title"></h3>
        <p id="fact-text"></p>
        <div id="industry-stories" hidden></div>
      </article>
      <p class="map-note" id="quiz-unlock-hint" role="status">「地形」と「産業・特産品」を ひらいてから クイズへ。</p>
      <button id="start-quiz" aria-describedby="quiz-unlock-hint" disabled>特徴クイズに すすむ</button>
    </div>
    <div id="phase-quiz" hidden>
      <p id="quiz-name"></p>
      <h2 id="quiz-prompt" tabindex="-1"></h2>
      <ul id="choices" aria-label="選択肢" role="list"></ul>
      <div id="quiz-voice">
        <p id="quiz-format"></p>
        <button id="quiz-mic" type="button" aria-describedby="quiz-format quiz-voice-status">🎙 声で答える</button>
        <p id="quiz-voice-status" role="status"></p>
      </div>
      <p id="quiz-feedback" role="status" hidden></p>
      <button id="next" hidden>つぎの問題</button>
    </div>
    <div class="actions">
      <button id="quit" class="secondary">トップへ戻る</button>
    </div>
  </section>
  <section id="result" hidden>
    <h2>都道府県 たんけん クリア！</h2>
    <p id="summary"></p><p id="result-sync" role="status"></p>
    <button id="again">トップへ戻る</button>
  </section>
</main>
<dialog id="medal-dialog" aria-labelledby="medal-title" aria-describedby="medal-status">
  <h2 id="medal-title">メダル</h2>
  <div id="medal-stamp" class="medal-stamp"><small id="medal-tier"></small><b>地</b><small>ち</small></div>
  <p id="medal-score"></p>
  <p id="medal-status" role="status"></p>
  <button id="medal-retry" class="secondary" hidden>もう一度 同期</button>
  <form method="dialog"><button type="submit">とじる</button></form>
</dialog>
<footer>
  地図の出典
  <a href="https://github.com/dataofjapan/land" target="_blank" rel="noopener">都道府県の輪郭</a>・
  <a href="https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W05.html" target="_blank" rel="noopener">国土数値情報「河川」</a>・
  <a href="https://www.gsi.go.jp/kihonjohochousa/kihonjohochousa41139.html" target="_blank" rel="noopener">国土地理院「日本の主な山岳標高」</a>・
  <a href="https://geo.maderaojen.me/en/" target="_blank" rel="noopener">国土数値情報「行政区域」加工データ</a>。
  <details><summary>産業・特産品の参考資料</summary>
    <a href="https://www.yaruki-assist.com/tips/regular-exam/post-2/" target="_blank" rel="noopener noreferrer">やる気アシスト</a>・
    <a href="https://manchiri.com/chuugaku/hokkaido/" target="_blank" rel="noopener noreferrer">マンガでわかる中学地理</a>・
    <a href="https://note.com/eikouroom/n/ne2f853700528" target="_blank" rel="noopener noreferrer">永高の中学受験部屋</a>・
    <a href="https://testea.net/chugaku-juken/tirihoxtukaidou/" target="_blank" rel="noopener noreferrer">TESTEA</a>・
    <a href="https://www.maff.go.jp/j/kanbo/tiho/todouhuken_gaiyou2022.html" target="_blank" rel="noopener noreferrer">農林水産省の都道府県資料</a>・
    <a href="https://www.meti.go.jp/statistics/tyo/kkj/seizo_result.html" target="_blank" rel="noopener noreferrer">経済産業省の製造業統計</a>。
  </details>
  地形の着色は学習用の目安です。<a href="https://www.gsi.go.jp/bousaichiri/lc_index.html" target="_blank" rel="noopener noreferrer">国土地理院の土地条件図</a>。産地の資料は、<a href="https://www.maff.go.jp/j/kanbo/tiho/todouhuken_gaiyou2022.html" target="_blank" rel="noopener">農林水産省の都道府県資料</a>などを参照しています。
</footer>
<script>
"use strict";

const $ = id => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";
const PREFIX = "chokomana-geography-v1:";
const BOARD = "0 0 755 635";
const IDLE = 180000;
const time = () => new Date().toISOString();
const uuid = () => crypto.randomUUID();
const device = load("device") || [...crypto.getRandomValues(new Uint8Array(32))]
  .map(v => v.toString(16).padStart(2, "0")).join("");
let storageWorks = save("device", device), args, profile, owner = "local";
let pending, hello = "waiting", attempt, stage = "menu", armed, drag, options;
let zoomed = false, keyboard = -1, activeSince, lastActivity, idleTimer, paths = new Map(), prefectures, menus;
let cache, medalResult, planLaunchHandled = false;
let autoVoice = true;
let quizListener;
const QuizRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function load(key) {
  try { return JSON.parse(localStorage.getItem(PREFIX + key)); }
  catch { return null; }
}
function save(key, value) {
  try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); return true; }
  catch { return false; }
}
function persist() {
  if (!args || !cache) return;
  cache.active = attempt || null;
  storageWorks = save(owner, cache);
  updateConnection();
}
function post(type, values = {}) {
  parent.postMessage({isStreamlitMessage:true, type:"streamlit:" + type, ...values}, "*");
}
function send(action, extra = {}) {
  if (pending) return;
  const id = uuid();
  pending = {id, action, started:performance.now(), timer: setTimeout(() => {
    pending = null;
    hello = "retry";
    diagnostic("request",{operation:action,outcome:"timeout",ms:26000});
    if (action === "sync" && medalResult?.mode==="saving") setMedalMode("retry");
    if (action === "hello" && !cache) selectOwner("local");
    updateConnection();
  }, 26000)};
  post("setComponentValue", {value:{id, action, device, ...extra}, dataType:"json"});
}
function updateConnection() {
  const waiting = cache?.queue.length || 0;
  const label = profile ? (hello === "relink" ? "ホームから開き直して学習記録を同期してください。"
    : hello === "invalid" ? "保存できない記録があります。ログを端末に保存できます。"
    : waiting ? (hello === "retry" ? `同期できませんでした。再同期できます（${waiting}件）。` : `同期待ち ${waiting}件`) : "ちょこまなと連携中")
    : ({waiting:"学習記録を準備中…", invalid_ticket:"起動リンクを確認できません。ホームから開き直してください。",
        retry:"通信を確認できません。端末内で学習できます。", local:"この端末に学習記録を保存します。"}[hello] || "");
  $("connection").textContent = label + (cache?.rejected && hello !== "invalid" ? " 未同期の記録あり。" : "") + (storageWorks ? "" : " ブラウザを閉じると未同期の記録は消えます。");
  $("retry").hidden = !["retry", "invalid_ticket"].includes(hello) && !waiting;
  $("retry").disabled = !!pending;
}
function sync() {
  if (profile && cache.queue.length && !pending) {
    send("sync", {profile, attempt:cache.queue[0]});
    updateConnection();
  }
}
function selectOwner(next) {
  if (cache && next === owner) return;
  if (attempt && cache) { stopTime(); persist(); }
  owner = next;
  cache = load(owner) || {queue:[], history:[], active:null};
  attempt = cache.active;
  zoomed = false;
  if (attempt && (!menuForVersion(attempt.menu, attempt.content_version)?.prefectures.includes(attempt.pref)
      || !["map","explore","quiz"].includes(attempt.phase))) {
    cache.previous_active = attempt;
    attempt = null;
    persist();
  }
  showMenu();
}
function receive(event) {
  if (event.source !== parent || event.data?.type !== "streamlit:render") return;
  const oldGraduation = JSON.stringify(args?.graduated_units || []);
  args = event.data.args;
  if (!prefectures) init();
  else if (stage === "menu" && oldGraduation !== JSON.stringify(args.graduated_units || [])) showMenu();
  const ack = args.ack;
  if (ack && ack.id === pending?.id) {
    const action = pending.action;
    diagnostic("request",{operation:action,outcome:ack.status,stage:ack.stage || action,code:ack.http_status || null,
      db_code:ack.db_code, failure:ack.failure, column:ack.column, constraint:ack.constraint,
      ms:Math.round(performance.now()-pending.started)});
    clearTimeout(pending.timer);
    pending = null;
    hello = ack.status;
    if (action === "hello") {
      profile = args.profile || null;
      selectOwner(profile || "local");
      if (ack.status !== "linked" || !startAssignedCourse()) {
        if (stage === "menu") showMenu();
      }
      if (profile) sync();
    } else if (ack.status === "saved") {
      cache.queue = cache.queue.filter(item => item.id !== ack.attempt_id);
      if (medalResult?.id===ack.attempt_id && ack.medal_saved) setMedalMode("saved");
      persist();
      sync();
    } else if (medalResult?.mode==="saving") {
      setMedalMode(ack.status==="relink" ? "relink" : ack.status==="invalid" ? "invalid" : "retry");
    }
  }
  updateConnection();
}
function shuffled(values) {
  values = [...values];
  for (let i = values.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [values[i], values[j]] = [values[j], values[i]];
  }
  return values;
}
function init() {
  prefectures = new Map(args.map.map(p => [p.id, p]));
  menus = new Map(args.menus.map(menu => [menu.menu_id, menu]));
  for (const pref of prefectures.values()) {
    const path = document.createElementNS(SVG, "path");
    path.setAttribute("d", pref.path);
    path.setAttribute("fill-rule", "evenodd");
    path.dataset.id = pref.id;
    $("outlines").append(path);
    paths.set(pref.id, path);
  }
  const ages = Array.from({length:11}, (_,i)=> {
    const choice = document.createElement("option");
    choice.value = String(i+1);
    choice.textContent = i === 10 ? "11さい いじょう" : `${i+1}さい`;
    return choice;
  });
  $("age").replaceChildren(...ages);
  updateVoiceControl();
  diagnostic("ui_ready",{build:args.build,touch:navigator.maxTouchPoints>0,screen_width:window.innerWidth});
  if (args.catalog_status) diagnostic("request",args.catalog_status);
  if (args.configured) send("hello");
  else {
    hello = "local";
    selectOwner("local");
  }
}
function display(next) {
  if (stage !== next) {
    if (next !== "game") stopQuizListening();
    if (next === "menu") cancelSpeech();
    diagnostic("screen",{view:next});
  }
  stage = next;
  for (const name of ["menu", "game", "result"]) $(name).hidden = name !== next;
}
function ageValue() {
  return Number(args.age || cache.age || 6);
}
const AREA_LABELS = {
  hokkaido:"北海道", tohoku:"東北", kanto:"関東", chubu:"中部", kinki:"近畿",
  chugoku:"中国", shikoku:"四国", kyushu:"九州", okinawa:"沖縄",
};
function courseAreas(menu) {
  if (menu.region === "north") return [
    {key:"hokkaido", ids:["01"]}, {key:"tohoku", ids:menu.prefectures.filter(id=>id !== "01")},
  ];
  if (menu.region === "kyushu") return [
    {key:"kyushu", ids:menu.prefectures.filter(id=>id !== "47")}, {key:"okinawa", ids:["47"]},
  ];
  return menu.region === "all" ? [] : [{key:menu.region, ids:menu.prefectures}];
}
function availableCourses() {
  const age = ageValue();
  return args.menus.filter(menu => menu.age_min <= age && age <= menu.age_max);
}
function completedPrefectures(regionalOnly) {
  return new Set(cache.history.filter(item => {
    if (item.status !== "completed") return false;
    if (!regionalOnly) return true;
    const menu = menus.get(item.menu);
    return menu && menu.region !== "all" && menu.prefectures.includes(item.pref);
  }).map(item => item.pref));
}
function nationalCourseUnlocked() {
  const regional = availableCourses().filter(menu => menu.region !== "all");
  const completed = completedPrefectures(true);
  return regional.length > 0 && regional.every(menu =>
    cmCourseIsGraduated(menu) || menu.prefectures.every(id => completed.has(id)));
}
function canOpenCourse(menu) {
  return Boolean(menu && (menu.region !== "all" || nationalCourseUnlocked()));
}
function beginCourse(menu, area, assignment = null, contentVersion = args.version) {
  if (!canOpenCourse(menu) || cmCourseIsGraduated(menu)) return;
  if (attempt) finish("abandoned");
  const ids = area?.ids || menu.prefectures;
  const learned = completedPrefectures(menu.region !== "all");
  const fresh = ids.filter(id => !learned.has(id));
  attempt = {id:uuid(), menu:menu.menu_id, pref:shuffled(fresh.length ? fresh : ids)[0], started:time(),
    content_version:contentVersion,
    area:area?.key || null, mapZoomed:menu.region !== "all", phase:"map",
    actions:[], intervals:[], questions:[], assignment};
  medalResult = null;
  showQuestion();
  readCurrent();
}
function cmGraduationBadge(){
  const badge=document.createElement('span');
  badge.className='cm-graduation-badge';
  badge.setAttribute('aria-label','修了');
  badge.textContent='🌸 修了';
  return badge;
}
function cmCourseIsGraduated(menu){return (args.graduated_units||[]).includes(menu?.menu_id)}
function cmCourseButton(menu,label,sublabel,run){
  const button=courseButton(label,sublabel,run);
  if(cmCourseIsGraduated(menu)){
    button.disabled=true;
    button.classList.add('cm-graduation-complete');
    button.append(cmGraduationBadge());
  }
  return button;
}

function courseButton(label, sublabel, run) {
  const button = document.createElement("button");
  button.textContent = label;
  const count = document.createElement("small");
  count.textContent = sublabel;
  button.append(count);
  button.onclick = run;
  return button;
}
function menuForVersion(id, version) {
  if (version === args.version) return menus.get(id);
  if (version === args.previous_version) return args.previous_menus.find(menu => menu.menu_id === id);
  return null;
}
function assignedCourse() {
  const assignment = args.assignment;
  if (!assignment?.plan_item_id) return null;
  const menu = menuForVersion(assignment.menu_id, assignment.content_version);
  return menu?.prefectures.length && canOpenCourse(menu) ? {assignment, menu} : null;
}
function startAssignedCourse() {
  if (!args.plan_launch || !profile || planLaunchHandled || stage !== "menu") return false;
  const course = assignedCourse();
  if (!course || cmCourseIsGraduated(course.menu)) return false;
  const {assignment, menu} = course;
  planLaunchHandled = true;
  if (attempt?.assignment === assignment.plan_item_id && attempt.menu === menu.menu_id
      && attempt.content_version === assignment.content_version) {
    showQuestion();
    readCurrent();
  } else {
    beginCourse(menu, null, assignment.plan_item_id, assignment.content_version);
  }
  return true;
}
function showMenu() {
  display("menu");
  const age = ageValue();
  $("age").value = String(Math.min(age,11));
  $("age").disabled = Boolean(args.age);
  $("resume").hidden = !attempt || !canOpenCourse(menus.get(attempt.menu));
  const course = assignedCourse();
  $("assigned-course").hidden = !course;
  if (course) {
    const {assignment, menu} = course;
    $("assigned-course").replaceChildren(cmCourseButton(menu, "きょうの課題　"+menu.region_label,
      `1つの都道府県・${menu.planned_question_count}問`,
      () => beginCourse(menu, null, assignment.plan_item_id, assignment.content_version)));
  }
  const list = availableCourses();
  const national = list.find(menu => menu.region === "all");
  const nationalButton = $("national-course");
  nationalButton.hidden = !canOpenCourse(national);
  nationalButton.disabled = nationalButton.hidden || cmCourseIsGraduated(national);
  nationalButton.onclick = () => beginCourse(national, null);
  nationalButton.querySelector('.cm-graduation-badge')?.remove();
  if (!nationalButton.hidden && cmCourseIsGraduated(national)) nationalButton.append(cmGraduationBadge());
  $("courses").replaceChildren(...list.flatMap(menu => courseAreas(menu).map(area =>
    cmCourseButton(menu, AREA_LABELS[area.key], `1つの都道府県・${menu.planned_question_count}問`,
      () => beginCourse(menu, area)))));
}
function areaForAttempt() {
  const menu = menus.get(attempt.menu);
  const region = menu.region === "all"
    ? [...menus.values()].find(item => item.region !== "all" && item.prefectures.includes(attempt.pref))
    : menu;
  const areas = courseAreas(region);
  return areas.find(area=>area.key === attempt.area && area.ids.includes(attempt.pref))
    || areas.find(area=>area.ids.includes(attempt.pref));
}
function wake() {
  if (stage !== "game" || !attempt || document.hidden) return;
  clearTimeout(idleTimer);
  const now = Date.now();
  if (activeSince !== undefined && now - lastActivity >= IDLE) stopTime();
  if (activeSince === undefined) activeSince = now;
  lastActivity = now;
  idleTimer = setTimeout(() => { stopTime(); persist(); }, IDLE);
}
function stopTime() {
  clearTimeout(idleTimer);
  if (activeSince === undefined || !attempt) return;
  let cursor = activeSince;
  const end = Math.min(Date.now(), lastActivity + IDLE);
  while (cursor < end) {
    const next = Math.min(cursor + IDLE, end);
    attempt.intervals.push([new Date(cursor).toISOString(),new Date(next).toISOString()]);
    cursor = next;
  }
  activeSince = undefined;
}
function current() { return attempt; }
function placed() { return attempt.actions.some(a => a.type === "placement" && a.target === attempt.pref); }
function containsHint() { return attempt.actions.some(a => a.type === "hint"); }
function info() { return args.discovery[attempt.pref]; }
function quizQuestions() {
  return attempt.content_version === args.previous_version ? info().previous_questions : info().questions;
}
function canStartQuiz() { return attempt?.phase === "explore" && didOpen("land") && didOpen("industry"); }
function didOpen(key) { return attempt.actions.some(a => a.type === "explore" && a.feature === key); }
function showQuestion() {
  const pref = prefectures.get(attempt.pref);
  for (const phase of ["map","explore","quiz"]) $("phase-"+phase).hidden = attempt.phase !== phase;
  $("course").textContent = ({
    map:"1　ピースを はめる", explore:"2　地図を たんけん", quiz:"3　とくちょうに ちょうせん",
  })[attempt.phase];
  const total = menuForVersion(attempt.menu, attempt.content_version).planned_question_count;
  $("count").textContent = attempt.phase === "quiz" ? `${attempt.questions.length} / ${total}` : "";
  display("game");
  if (attempt.phase === "map") {
    armed = false;
    drag = null;
    keyboard = -1;
    const [x,y,w,h] = pref.bounds;
    const scale = Math.min(96/w, 70/h);
    const left = (120-w*scale)/2-x*scale, top = (90-h*scale)/2-y*scale;
    $("pieceLayer").setAttribute("transform", `translate(${left} ${top}) scale(${scale})`);
    $("piecePath").setAttribute("d", pref.path);
    zoomed = attempt.mapZoomed ?? (menus.get(attempt.menu).region !== "all");
    $("ghost").setAttribute("d", pref.path);
    $("ghost").setAttribute("visibility","hidden");
    $("feedback").textContent = "ドラッグするか、ピースと置く場所を順にタップ。";
    drawQuestion();
    updateMap();
  } else if (attempt.phase === "explore") {
    drawExplore(pref);
  } else {
    drawQuiz();
  }
  wake();
  persist();
}
function updateMap() {
  const area = areaForAttempt();
  let box = BOARD;
  if (zoomed) {
    const members = area.ids.map(id => prefectures.get(id).bounds);
    const x0 = Math.min(...members.map(b=>b[0]))-18, y0 = Math.min(...members.map(b=>b[1]))-18;
    const w = Math.max(...members.map(b=>b[0]+b[2]))+18-x0, h = Math.max(...members.map(b=>b[1]+b[3]))+18-y0;
    box = [x0,y0,w,h].join(" ");
  }
  $("map").setAttribute("viewBox", box);
  $("inset").style.display = zoomed ? "none" : "";
  $("board-label").textContent = zoomed ? AREA_LABELS[area.key] + "の地図" : "日本全体";
  $("zoom").textContent = zoomed ? "全国の地図" : "地方の地図";
}
function drawQuestion() {
  const solved = placed();
  const hint = !solved && containsHint();
  const highlight = !solved && keyboard >= 0 ? [...paths.keys()][keyboard] : null;
  $("placement-recall").hidden = !solved;
  $("prompt").hidden = $("placement-tray").hidden = $("feedback").hidden = solved;
  $("placement-map").classList.toggle("is-placed",solved);
  $("map").setAttribute("tabindex",solved ? "-1" : "0");
  $("map").setAttribute("aria-label",solved
    ? "日本地図。正しくはめた都道府県が色で示されています。"
    : "日本地図。地図にピースをはめる。矢印キーで候補を移動し、Enterでおく。");
  for (const [id,path] of paths) {
    path.classList.toggle("found", solved && id === attempt.pref);
    path.classList.toggle("hinted", hint && id === attempt.pref);
    path.classList.toggle("keyboard", id === highlight);
  }
  $("piece").setAttribute("aria-pressed", String(!!armed));
  $("hint").disabled = hint;
  $("zoom").disabled = attempt.actions.length >= 195;
}
function put(target) {
  if (attempt?.phase !== "map" || placed()) return;
  wake();
  const actions = attempt.actions;
  if (actions.length >= 195 && target !== attempt.pref) {
    $("feedback").textContent = "ヒントで 場所を たしかめよう。";
    return;
  }
  actions.push({type:"placement", target, at:time()});
  armed = false;
  diagnostic("piece_placement",{onMapLand:target!==null});
  if (target === attempt.pref) {
    drawQuestion();
    $("recall-prompt").focus();
    readCurrent();
  } else {
    drawQuestion();
    $("feedback").textContent = "まだ はまらないね。形や となりを 見くらべよう。";
    speakText($("feedback").textContent);
  }
  persist();
}
function revealPrefecture() {
  if (attempt?.phase !== "map" || !placed()) return;
  attempt.phase = "explore";
  attempt.view = "capital";
  attempt.actions.push({type:"explore",feature:"capital",at:time()});
  showQuestion();
  $("pref-name").focus();
  readCurrent({announcePrefecture:true});
}
const INDUSTRY_ICONS = {
  cow:'<path fill="#fffaf0" d="M5 9 2 5l6 1 2-3h4l2 3 6-1-3 5v6a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4Z"/><path fill="#bf7651" d="M5 9l3-2 2 4-3 3H5Zm10-2 3 1 1 3-4 2-2-3Z"/><rect x="7" y="13" width="10" height="6" rx="3" fill="#f4b6ae"/><path d="M10 16h.1m3.9 0h.1"/>',
  apple:'<path fill="#e46649" d="M12 8c4-4 10-1 9 5s-4 9-9 7c-5 2-8-1-9-7S8 4 12 8Z"/><path d="M12 8c0-3-1-4-2-5m2 4c1-3 4-4 7-3-1 2-4 3-7 3" fill="#82aa60"/>',
  citrus:'<path fill="#eea453" d="M3 13c0-5 4-7 9-7s9 2 9 7-4 8-9 8-9-3-9-8Z"/><path fill="#83a661" d="M12 6c0-2 3-4 7-4-1 3-3 4-7 4Z"/>',
  fruit:'<path fill="#f4a770" d="M12 7c4-4 9 0 9 4 0 5-4 9-9 11-5-2-9-6-9-11 0-4 5-8 9-4Z"/><path d="M12 7c-1-3 3-5 6-4-1 2-3 4-6 4m0 0c-3 4-3 8 0 12"/>',
  cherry:'<circle cx="7" cy="16" r="4" fill="#e65c5b"/><circle cx="17" cy="17" r="4" fill="#e65c5b"/><path d="M7 12c5-3 5-6 5-10 2 5 5 6 5 11m-5-9c3-2 6-2 9-1"/>',
  grape:'<path d="M12 7c0-2 1-4 4-5"/><g fill="#a785c1"><circle cx="8" cy="10" r="4"/><circle cx="16" cy="10" r="4"/><circle cx="12" cy="14" r="4"/><circle cx="12" cy="18" r="3"/></g>',
  rice:'<path d="M6 22c4-2 8-6 9-17"/><g fill="#e5b955"><path d="M14 10c-5 0-6-3-6-6 4 1 6 2 6 6Zm-2 5c-5 0-7-2-7-5 5 0 7 2 7 5Zm4-7c1-4 3-5 6-6-1 4-3 6-6 6Zm-2 6c2-4 4-5 8-5-1 4-4 5-8 5Zm-3 5c2-4 5-5 9-5-2 4-5 5-9 5Z"/></g>',
  leaf:'<path fill="#83b375" d="M3 19C2 7 13 4 21 4c-1 10-5 16-15 15Z"/><path d="M3 21 17 9m-7 6v-4m3 2h4"/>',
  root:'<path fill="#c98a64" d="M16 7c4 4 3 6-1 10-3 3-6 4-12 5 1-6 2-9 5-12 4-4 6-5 8-3Z"/><path d="m16 7 3-5m-1 6 4-2m-13 7 2 2m-5 2 2 2"/>',
  tea:'<path fill="#c9e1ab" d="M4 11h14l-1 7a4 4 0 0 1-4 3H9a4 4 0 0 1-4-3Z"/><path d="M18 12h2a2 2 0 0 1 0 4h-2M8 8c2-3-1-4 1-6m4 6c2-3-1-4 1-6"/>',
  fish:'<path fill="#72b6d7" d="M2 12c4-6 10-7 15-2l5-4v12l-5-4c-5 5-11 4-15-2Z"/><path d="M7 11h.1m4-3c2 2 2 6 0 8"/>',
  shell:'<path fill="#ebbb99" d="M3 11a9 9 0 0 1 18 0l-7 9h-4Z"/><path d="m7 8 4 11m2-14-1 14m6-11-5 11"/>',
  pearl:'<path fill="#d7b3d6" d="M2 12c2-7 18-7 20 0l-5 7H7Z"/><circle cx="12" cy="11" r="4" fill="#fffaf4"/>',
  crab:'<path fill="#ec8870" d="M5 13c0-4 4-6 7-6s7 2 7 6-4 5-7 5-7-1-7-5Z"/><path d="m5 12-3-2V6m17 6 3-2V6M7 17l-4 4m14-4 4 4m-11-10h.1m3.9 0h.1"/>',
  melon:'<circle cx="12" cy="13" r="8" fill="#b7ca76"/><path d="M12 5V2m-4 0h8M5 11l10 9M8 6l11 10M6 17 16 6m-6 14 10-10"/>',
  onion:'<path fill="#edba7b" d="M12 5c2 4 8 5 8 10 0 4-3 6-8 6s-8-2-8-6c0-5 6-6 8-10Z"/><path d="M12 6V2m0 6c-5 4-6 8-2 11m2-11c5 4 6 8 2 11"/>',
  greenhouse:'<path fill="#daead6" d="M2 21v-9l10-8 10 8v9Z"/><path d="M12 4v17M2 12h20m-15 9v-7m10 7v-7"/>',
  seaweed:'<path fill="#91aa76" d="M5 21c4-6-4-10 0-16 5 3 5 7 4 11 4-3 0-9 3-14 5 2 5 7 3 11 3-2 3-5 6-7 2 7-4 12-7 15Z"/>',
  mushroom:'<path fill="#c8895e" d="M2 12c0-6 4-9 10-9s10 3 10 9Z"/><path fill="#fdf2cc" d="M9 12h6l2 7c-3 3-7 3-10 0Z"/>',
  cane:'<path d="M9 22c3-6 4-13 4-21m-1 8c-1-3-5-5-9-4m9 5c3-4 6-5 9-4m-11 9c-2-3-5-4-8-3m8 4c4-4 7-4 11-3" stroke="#5c8737" stroke-width="2.3"/>',
};
const FACT_WIDTH = 560, FACT_HEIGHT = 330;
function svgNode(tag, attrs = {}) {
  const node = document.createElementNS(SVG,tag);
  for (const [name,value] of Object.entries(attrs)) node.setAttribute(name,value);
  return node;
}
function featureControl(node, label, action) {
  node.setAttribute("tabindex","0");
  node.setAttribute("role","button");
  node.setAttribute("aria-label",label);
  node.append(Object.assign(svgNode("title"),{textContent:label}));
  node.onclick = action;
  node.onkeydown = event => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); action(); }
  };
  return node;
}
function renderFactNeighbors(pref, item, transform, toMap, scale, tx, ty) {
  const shapes = $("fact-neighbors"), labels = $("fact-neighbor-names");
  if (shapes.dataset.prefecture === pref.id) return;
  shapes.dataset.prefecture = pref.id;
  shapes.replaceChildren();
  labels.replaceChildren();
  const land = item.land_neighbors.map(id => prefectures.get(id));
  const sea = item.sea_neighbors.map(id => prefectures.get(id));
  $("nearby-prefectures").hidden = !land.length && !sea.length;
  $("land-neighbor-list").hidden = !land.length;
  $("sea-neighbor-list").hidden = !sea.length;
  $("land-neighbor-list").textContent = "県境を接する："+land.map(p => p.name).join("・");
  $("sea-neighbor-list").textContent = "海をはさんで近い："+sea.map(p => p.name).join("・");
  const focus = $("fact-shape");
  const used = [];
  const point = new DOMPoint();
  const contains = (path, x, y) => {
    point.x = (x-tx)/scale;
    point.y = (y-ty)/scale;
    return path.isPointInFill(point);
  };
  const paths = [...land,...sea].map(neighbor => {
    const path = svgNode("path",{d:neighbor.path,transform,class:"neighbor-shape","fill-rule":"evenodd"});
    shapes.append(path);
    return [neighbor,path];
  });
  for (const [neighbor,path] of paths) {
    const [bx,by,bw,bh] = neighbor.bounds;
    const [x0,y0] = toMap([bx,by]), [x1,y1] = toMap([bx+bw,by+bh]);
    const half = neighbor.name.length*8.5;
    const left = Math.max(x0,half+4), right = Math.min(x1,FACT_WIDTH-half-4);
    const top = Math.max(y0,12), bottom = Math.min(y1,FACT_HEIGHT-12);
    const centerX = (left+right)/2, centerY = (top+bottom)/2;
    let best = null;
    // Prefer a position fully inside the visible neighbor, away from the selected prefecture.
    for (let y=top; y<=bottom; y+=8) {
      for (let x=left; x<=right; x+=8) {
        if (!contains(path,x,y) || contains(focus,x,y)) continue;
        if (used.some(p => Math.abs(p.x-x) < p.half+half+4 && Math.abs(p.y-y)<20)) continue;
        const sides = [x-half,x+half];
        const covered = sides.filter(edge => contains(path,edge,y)).length;
        const crossed = sides.filter(edge => contains(focus,edge,y)).length;
        const score = covered*40-crossed*65-Math.hypot(x-centerX,y-centerY)*.32;
        if (!best || score>best.score) best = {x,y,half,score};
      }
    }
    if (!best) continue;
    used.push(best);
    const label = svgNode("text",{x:best.x,y:best.y,class:"neighbor-name",
      "dominant-baseline":"central","text-anchor":"middle"});
    label.textContent = neighbor.name;
    labels.append(label);
  }
}

function mapWater(pref, item, toMap, scale, tx, ty) {
  const water = $("fact-water");
  if (water.dataset.prefecture === pref.id) return;
  water.dataset.prefecture = pref.id;
  water.replaceChildren();
  const paths = [$("fact-shape"), ...$("fact-neighbors").children];
  const point = new DOMPoint();
  const onLand = (x,y) => {
    point.x = (x-tx)/scale;
    point.y = (y-ty)/scale;
    return paths.some(path => path.isPointInFill(point));
  };
  const labels = [];
  for (const sea of item.seas) {
    const [nearX,nearY] = toMap(sea.point);
    const narrow = sea.name.endsWith("湾");
    const step = narrow ? 4 : 8;
    const half = (narrow ? 6 : 8)*sea.name.length;
    const x0 = Math.min(FACT_WIDTH-half-8,Math.max(half+8,nearX));
    const y0 = Math.min(FACT_HEIGHT-18,Math.max(18,nearY));
    let nearest = Infinity, location;
    for (let y = Math.max(18,y0-48); y <= Math.min(FACT_HEIGHT-18,y0+48); y += step) {
      for (let x = Math.max(half+8,x0-64); x <= Math.min(FACT_WIDTH-half-8,x0+64); x += step) {
        if ([-half,0,half].some(dx => [-7,7].some(dy => onLand(x+dx,y+dy)))) continue;
        if (labels.some(label => Math.abs(x-label.x)<half+label.half+10 && Math.abs(y-label.y)<23)) continue;
        const distance = Math.hypot(x-x0,y-y0);
        if (distance < nearest) { nearest = distance; location = {x,y,half}; }
      }
    }
    if (!location) continue;
    labels.push(location);
    const label = svgNode("text",{x:location.x,y:location.y,class:narrow?"sea-name bay-name":"sea-name",
      "text-anchor":"middle","dominant-baseline":"central"});
    label.textContent = sea.name;
    water.append(label);
  }
}

function mapStories(item) {
  return item.industry_stories.map((story,index)=>({...story, number:index+1}));
}
function selectedMapStory(stories) {
  return stories.find(story=>story.key===attempt.mapStory) || stories[0];
}
function selectMapStory(key, focusChoice = true) {
  if (attempt?.phase !== "explore" || attempt.view !== "industry") return;
  const item = info();
  if (!mapStories(item).some(story=>story.key===key)) return;
  wake();
  attempt.mapStory = key;
  renderFactMap(prefectures.get(attempt.pref),item,"industry");
  if (focusChoice) $("map-industry-shortcuts").querySelector(`button[data-story="${key}"]`)?.focus({preventScroll:true});
  readCurrent();
  persist();
}
function renderIndustryShortcuts(pref, stories, active) {
  const shortcuts = $("map-industry-shortcuts");
  $("fact-map-panel").classList.toggle("has-industry-shortcuts",Boolean(active));
  shortcuts.hidden = !active;
  if (!active) return;
  if (shortcuts.dataset.prefecture !== pref.id) {
    shortcuts.dataset.prefecture = pref.id;
    shortcuts.replaceChildren(...stories.map(story=>{
      const pick = document.createElement("button");
      pick.type = "button";
      pick.className = "secondary";
      pick.dataset.story = story.key;
      pick.textContent = `${story.number}. ${story.name}`;
      pick.onclick = () => selectMapStory(story.key);
      return pick;
    }));
  }
  for (const pick of shortcuts.children) pick.setAttribute("aria-pressed",String(pick.dataset.story===active.key));
}

function factMapProjection(pref) {
  // Tokyo's remote islands make mainland landmarks too small in the national bounds.
  const [x,y,w,h] = pref.id === "13" ? [346,344,32,21] : pref.bounds;
  const scale = Math.min((FACT_WIDTH-144)/w,(FACT_HEIGHT-92)/h);
  const tx = FACT_WIDTH/2-(x+w/2)*scale, ty = FACT_HEIGHT/2-(y+h/2)*scale;
  return {scale,tx,ty,transform:`translate(${tx} ${ty}) scale(${scale})`,
    toMap:([px,py])=>[tx+px*scale,ty+py*scale]};
}
// Reserve boxes in viewBox coordinates so the layout scales without introducing collisions.
function reserveMapPosition(point, width, height, occupied) {
  const [x,y] = point;
  const inside = (cx,cy) => cx-width/2 >= 4 && cx+width/2 <= FACT_WIDTH-4 &&
    cy-height/2 >= 4 && cy+height/2 <= FACT_HEIGHT-4;
  const free = (cx,cy) => inside(cx,cy) && !occupied.some(box =>
    Math.abs(cx-box.x)*2 < width+box.width+6 && Math.abs(cy-box.y)*2 < height+box.height+6);
  let position = free(x,y) ? [x,y] : null;
  for (let radius=12; !position && radius<=120; radius+=12) {
    for (let step=0; step<12; step++) {
      const angle = -Math.PI/2 + step*Math.PI/6;
      const cx = x+Math.cos(angle)*radius, cy = y+Math.sin(angle)*radius;
      if (free(cx,cy)) { position=[cx,cy]; break; }
    }
  }
  if (position) occupied.push({x:position[0],y:position[1],width,height});
  return position;
}

function addMapLeader(from, to, offset) {
  const [x1,y1] = from, [x2,y2] = to;
  const distance = Math.hypot(x2-x1,y2-y1);
  if (distance <= offset+5) return;
  const end = 1-offset/distance;
  $("fact-leaders").append(
    svgNode("line",{x1,y1,x2:x1+(x2-x1)*end,y2:y1+(y2-y1)*end,class:"map-leader"}),
    svgNode("circle",{cx:x1,cy:y1,r:2.4,class:"map-leader-dot"}));
}

function renderTerrainLabels(features, occupied) {
  for (const {name,point,kind,primary} of features) {
    const size = primary ? 19 : 17;
    const width = name.length*size+4;
    const offset = kind==="peak" ? 28 : 13;
    const position = reserveMapPosition([point[0],point[1]-offset],width,size+4,occupied);
    if (!position) continue;
    const label = svgNode("text",{x:position[0],y:position[1],
      class:"place-reference "+(primary?"primary-land":"secondary-land")+" "+kind+"-name",
      style:`font-size:${size}px`,"text-anchor":"middle","dominant-baseline":"central"});
    label.textContent = name;
    if (Math.hypot(position[0]-point[0],position[1]-point[1]+offset)>16) {
      addMapLeader(point,position,12);
    }
    $("fact-terrain-labels").append(label);
  }
}

function renderIndustryMap(pref,item,projection,occupied) {
  const {toMap} = projection;
  const stories = mapStories(item);
  const active = selectedMapStory(stories);
  renderIndustryShortcuts(pref,stories,active);
  renderIndustryStories(pref,stories,active);
  const regions = $("fact-product-regions"), pins = $("fact-pins");
  const sites = stories.map(story=>({story,label:story.place.label,point:story.place.point}));
  for (const {story,label,point} of sites) {
    const selected = story===active;
    const origin = toMap(point);
    const [cx,cy] = origin;
    if (story.place) regions.append(svgNode("circle",{cx,cy,r:selected?16:10,
      class:"map-production-region"+(selected?" active":"")}));
    const position = reserveMapPosition(origin,28,28,occupied);
    if (!position) continue;
    addMapLeader(origin,position,12);
    const marker = svgNode("g",{class:"production-marker"+(selected?" active":""),
      transform:`translate(${position.join(" ")})`});
    marker.append(svgNode("circle",{r:selected?13:11}),Object.assign(svgNode("text",{
      "font-size":selected?17:15,"text-anchor":"middle","dominant-baseline":"central",
    }),{textContent:String(story.number)}));
    pins.append(featureControl(marker,story.name+"："+label,()=>selectMapStory(story.key)));
  }
  $("industry-key-symbol").innerHTML = INDUSTRY_ICONS[active.icon] || '<circle cx="12" cy="12" r="7" fill="#83c6a2"/>';
  $("industry-name").textContent = active.name;
  $("map-caption").textContent = `${active.number}. ${active.name}：${active.place.label}（代表地）`;
}

function renderFactMap(pref, item, selected) {
  const projection = factMapProjection(pref);
  const {scale,tx,ty,transform,toMap} = projection;
  const industry = selected === "industry";
  $("fact-map").classList.toggle("terrain-context",industry);
  $("fact-shape").setAttribute("d",pref.path);
  $("fact-shape").setAttribute("transform",transform);
  renderFactNeighbors(pref,item,transform,toMap,scale,tx,ty);
  mapWater(pref,item,toMap,scale,tx,ty);
  if (selected !== "industry") renderIndustryShortcuts(pref);
  const extent = $("fact-land-extent");
  extent.setAttribute("hidden","");
  for (const id of ["fact-rivers","fact-peaks","fact-product-regions","fact-leaders","fact-terrain-labels","fact-pins","relief-controls"]) $(id).replaceChildren();
  $("relief-controls").hidden = $("relief-list-title").hidden = selected !== "land";
  $("terrain-key-group").hidden = selected === "capital";
  $("industry-key-group").hidden = selected !== "industry";
  $("capital-key-group").hidden = selected !== "capital";
  if (selected === "capital") {
    $("map-caption").textContent = "";
    const pin = svgNode("g",{class:"capital-point",transform:`translate(${toMap(item.capital_point).join(" ")})`});
    pin.append(svgNode("circle",{r:10}),Object.assign(svgNode("text",
      {"font-size":13,"dominant-baseline":"central","text-anchor":"middle"}),{textContent:"★"}));
    const [capitalX] = toMap(item.capital_point);
    const left = capitalX+18+16*item.capital.length > FACT_WIDTH;
    const name = svgNode("text",{class:"capital-name",x:left?-14:14,y:0,
      "dominant-baseline":"central","text-anchor":left?"end":"start"});
    name.textContent = item.capital;
    pin.append(name);
    $("fact-pins").append(pin);
    return;
  }
  const terrain = renderTerrain(item,projection,industry);
  if (industry) {
    renderIndustryMap(pref,item,projection,terrain.occupied);
    renderTerrainLabels(terrain.labels,terrain.occupied);
  }
}

function renderTerrain(item,{transform,toMap},industry) {
  const extent = $("fact-land-extent"), overlay = item.land_overlay;
  const rivers = [...item.rivers.entries()].filter(([,river]) =>
    item.core_rivers.includes(river.name) && river.name !== overlay?.alias);
  const peaks = [...item.peaks.entries()].filter(([,peak]) => item.core_peaks.includes(peak.name));
  $("relief-controls").hidden = $("relief-list-title").hidden = industry || (!overlay && !rivers.length && !peaks.length);
  $("terrain-key-group").textContent = rivers.length && peaks.length ? "川・山と地形" : "地形";
  const selectedRelief = industry ? null : attempt.relief;
  const mainRiver = rivers.find(([,feature]) => feature.name === item.land)?.[1];
  const mainPeak = peaks.find(([,feature]) => feature.name.startsWith(item.land))?.[1];
  const detail = selectedRelief?.kind==="river" ? rivers.find(([index])=>index===selectedRelief.index)?.[1] :
    selectedRelief?.kind==="peak" ? peaks.find(([index])=>index===selectedRelief.index)?.[1] : null;
  const hasRiver = Boolean(rivers.length || overlay?.kind === "river");
  const terrainKey = [
    overlay && overlay.kind !== "river" ? "色の範囲は目安" : "",
    hasRiver ? "青線は川" : "",
    peaks.length ? "山のマークは山頂" : "",
  ].filter(Boolean).join("・");
  if (industry) $("terrain-key-group").textContent = terrainKey;
  else $("map-caption").textContent = terrainKey;
  if (overlay) {
    extent.setAttribute("d",overlay.path);
    extent.setAttribute("transform",transform);
    const active = !industry && (!selectedRelief || selectedRelief.kind === "main");
    extent.setAttribute("class",overlay.kind === "river" ? "map-river"+(active ? " selected" : "") : "land-"+overlay.kind);
    // This group and the transformed clip share the same viewport coordinate space.
    // Applying the clip to the transformed path would transform the clip a second time.
    const clip = $("fact-land-clip");
    if (overlay.kind === "area" || overlay.kind === "river") clip.setAttribute("clip-path","url(#fact-clip)");
    else clip.removeAttribute("clip-path");
    extent.removeAttribute("hidden");
  }
  const [lx,ly] = toMap((mainPeak || mainRiver)?.point || item.land_point);
  const landLabel = svgNode("text",{
    x:Math.max(62,Math.min(FACT_WIDTH-62,lx)),y:Math.max(18,ly-(mainPeak ? 19 : 8)),
    class:"place-reference "+(detail && detail !== mainRiver && detail !== mainPeak ? "secondary-land" : "primary-land"),"text-anchor":"middle",
  });
  landLabel.textContent = item.land;
  if (!industry) $("fact-pins").append(landLabel);
  if (detail && detail !== mainRiver && detail !== mainPeak) {
    const [px,py] = toMap(detail.point);
    const label = svgNode("text",{x:Math.max(58,Math.min(FACT_WIDTH-58,px)),y:Math.max(17,py-18),
      class:"place-reference primary-land","text-anchor":"middle"});
    label.textContent = detail.name;
    $("fact-pins").append(label);
  }
  for (const [index, river] of rivers) {
    const path = svgNode("path",{d:river.path,transform,
      class:"map-river"+(detail===river || (!selectedRelief && mainRiver===river)?" selected":"")});
    if (industry) {
      $("fact-rivers").append(path);
    } else {
      const hit = svgNode("path",{d:river.path,transform,class:"river-hit"});
      const wrapper = svgNode("g");
      wrapper.append(path,hit);
      $("fact-rivers").append(featureControl(wrapper,river.name+"をみる",()=>openRelief("river",index)));
    }
  }
  for (const [index, peak] of peaks) {
    const pin = svgNode("g",{class:"map-peak"+(detail===peak || (!selectedRelief && mainPeak===peak)?" selected":""),
      transform:`translate(${toMap(peak.point).join(" ")})`});
    pin.append(svgNode("circle",{r:13}),
      svgNode("path",{class:"peak-back",d:"M-2 6 5-5 12 6Z"}),
      svgNode("path",{class:"peak-front",d:"M-11 7 -3-10 6 7Z"}),
      svgNode("path",{class:"peak-snow",d:"M-7-1 -3-9 1-1 -2-3 -4 0Z"}));
    $("fact-peaks").append(industry ? pin : featureControl(pin,peak.name+"をみる",()=>openRelief("peak",index)));
  }
  if (industry) {
    const occupied = [...$("fact-neighbor-names").children,...$("fact-water").children].map(label=>({
      x:Number(label.getAttribute("x")),y:Number(label.getAttribute("y")),
      width:label.textContent.length*16+4,height:20,
    }));
    for (const [,peak] of peaks) {
      const [x,y] = toMap(peak.point);
      occupied.push({x,y,width:26,height:26});
    }
    const labels = [
      {name:item.land,point:[lx,ly],kind:mainPeak?"peak":mainRiver || overlay?.kind==="river"?"river":"land",primary:true},
      ...rivers.filter(([,river])=>river!==mainRiver).map(([,river])=>({
        name:river.name,point:toMap(river.point),kind:"river",
      })),
      ...peaks.filter(([,peak])=>peak!==mainPeak).map(([,peak])=>({
        name:peak.name.split("＜")[0],point:toMap(peak.point),kind:"peak",
      })),
    ];
    return {occupied,labels};
  }
  const controls = [
    ...(overlay ? [["main",0,item.land]] : []),
    ...rivers.map(([i,f])=>["river",i,f.name]),
    ...peaks.map(([i,f])=>["peak",i,f.name]),
  ];
  for (const [kind,index,name] of controls) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary relief-"+(kind === "main" ? overlay.kind : kind);
    button.textContent = name;
    const active = selectedRelief ? selectedRelief.kind===kind && selectedRelief.index===index :
      kind==="main" || (kind==="river" && item.rivers[index]===mainRiver) ||
      (kind==="peak" && item.peaks[index]===mainPeak);
    button.setAttribute("aria-pressed",String(active));
    button.onclick = () => openRelief(kind,index);
    $("relief-controls").append(button);
  }
}
function openRelief(kind,index) {
  if (attempt?.phase !== "explore" || attempt.view !== "land") return;
  wake();
  attempt.relief = {kind,index};
  drawExplore(prefectures.get(attempt.pref));
  $("relief-controls").querySelector('[aria-pressed="true"]')?.focus({preventScroll:true});
  diagnostic("geography_detail",{type:kind});
  readCurrent();
  persist();
}
function speechAvailable() {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}
let waitingSpeech;
function japaneseVoice(voices) {
  const score = voice => {
    const name = `${voice.name} ${voice.voiceURI}`;
    return (/natural|neural|premium|enhanced|高品質/i.test(name) ? 100 : 0)
      + (/nanami|keita|google|日本語|kyoko|otoya/i.test(name) ? 12 : 0)
      + (voice.default ? 1 : 0);
  };
  return voices.filter(voice=>/^ja(?:[-_]|$)/i.test(voice.lang)).sort((a,b)=>score(b)-score(a))[0];
}
function cancelSpeech() {
  waitingSpeech = null;
  if (speechAvailable()) speechSynthesis.cancel();
}
function speakText(text, item = null) {
  if (stage === "menu" || quizListener || !autoVoice || !speechAvailable() || !text || document.hidden) return;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) { waitingSpeech={text,item}; return; }
  const voice = japaneseVoice(voices);
  if (!voice) {
    $("voice-label").textContent = "日本語音声なし";
    diagnostic("speech",{outcome:"error",code:"japanese-voice-unavailable"});
    return;
  }
  // Keep normal Japanese spelling and punctuation for the speech engine's phrasing.
  if (item) for (const [label,reading] of [[item.name,item.reading],[item.capital,item.capital_reading],
      [item.land,item.land_reading]]) {
    text = text.replaceAll(label+"（"+reading+"）",label);
  }
  const speech = new SpeechSynthesisUtterance(text);
  speech.voice = voice;
  speech.lang = voice.lang.replace("_","-"); speech.rate = .96;
  speech.onerror = event => {
    if (!["canceled","interrupted"].includes(event.error)) diagnostic("speech",{outcome:"error",code:event.error});
  };
  cancelSpeech();
  speechSynthesis.resume?.();
  speechSynthesis.speak(speech);
}
if (speechAvailable()) {
  speechSynthesis.addEventListener?.("voiceschanged",()=>{
    const pending = waitingSpeech;
    waitingSpeech = null;
    updateVoiceControl();
    if (pending) speakText(pending.text,pending.item);
  });
}
function updateVoiceControl() {
  const available = speechAvailable(), voices = available ? speechSynthesis.getVoices() : [];
  $("voice-toggle").disabled = !available;
  $("voice-toggle").checked = available && autoVoice;
  $("voice-label").textContent = !available ? "読み上げ未対応" :
    voices.length && !japaneseVoice(voices) ? "日本語音声なし" : "自動読み上げ";
}
function readCurrent({announcePrefecture = false} = {}) {
  if (stage === "game" && attempt?.phase === "map") {
    speakText(placed() ? $("recall-prompt").textContent :
      $("board-label").textContent+"。ピースを、地図のぴったりの場所へ。ドラッグするか、ピースと置く場所を順にタップ。");
  } else if (stage === "game" && attempt?.phase === "explore") {
    const item = info();
    if (attempt.view === "capital") {
      const prefecture = item.reading || item.name;
      const capital = item.capital_reading || item.capital;
      const introduction = announcePrefecture ? `これは${prefecture}です。` : "";
      speakText(`${introduction}${prefecture}の県庁所在地は、${capital}です。`,item);
    } else if (attempt.view === "industry") {
      const {name, reading, intro} = selectedMapStory(mapStories(item));
      speakText(`${reading || name}。${intro}`,item);
    } else {
      speakText([$("fact-title").textContent,$("fact-text").textContent].filter(Boolean).join("。"),item);
    }
  } else if (stage === "game" && attempt?.phase === "quiz") {
    const entry = attempt.questions.at(-1), q = quizQuestions()[attempt.questions.length-1], prefecture = info();
    const prompt = q.prompt.replaceAll(prefecture.name, prefecture.reading || prefecture.name);
    const text = entry.choice !== undefined ? $("quiz-feedback").textContent :
      prompt + " " + [...entry.options.map(key=>choiceVoiceForms(q.options[Number(key)])[0]),
        "選んだ名前を言ってね"].join("。");
    speakText(text,prefecture);
  } else if (stage === "result" && medalResult) {
    speakText($("medal-score").textContent,medalResult.info);
  }
}
function updateMedal() {
  if (!medalResult) return;
  const {grade,mode} = medalResult, label = grade === "gold" ? "金" : "銀";
  const pendingSave = mode==="saving";
  $("medal-stamp").className = "medal-stamp "+grade;
  $("medal-tier").textContent = label;
  $("medal-title").textContent = mode==="saved" ? `${label}メダルを ゲット！` :
    mode==="local" ? `${label}メダル！` : "都道府県たんけん クリア！";
  const status = ({saved:"ちょこまなの「今日の成果」に保存しました。",saving:"メダルを ちょこまなに保存しています。",
    retry:"同期できませんでした。記録は端末に残っています。再同期できます。",
    relink:"ちょこまなから開き直すと、この記録を送れます。",
    invalid:"記録形式を確認できません。記録は端末に残っています。",
    local:"この端末の記録です。" })[mode];
  $("medal-status").textContent = status;
  $("result-sync").textContent = status;
  $("medal-retry").hidden = mode !== "retry";
  $("medal-stamp").setAttribute("aria-label",label+"メダル");
  $("medal-dialog").setAttribute("aria-busy",String(pendingSave));
}
function setMedalMode(mode) {
  if (!medalResult || medalResult.mode==="saved") return;
  medalResult.mode = mode;
  updateMedal();
}
function diagnostic(event, data = {}) {
  try {
    const rows = load("ui-diagnostics") || [];
    rows.push({at:time(), event, ...data});
    save("ui-diagnostics", rows.slice(-250));
  } catch {}
}
function drawExplore(pref) {
  const item = info(), selected = attempt.view;
  $("pref-name").textContent = `${item.name}（${item.reading}）`;
  $("pref-capital").textContent = `都道府県庁所在地　${item.capital}（${item.capital_reading}）`;
  $("pref-capital").classList.toggle("supplement",selected !== "capital");
  renderFactMap(pref,item,selected);
  const facts = {
    capital: [item.capital+"（"+item.capital_reading+"）", ""],
    land: [item.land+"（"+item.land_reading+"）", item.climate+"。"],
    industry: ["産業・特産品", ""],
  };
  const relief = attempt.relief;
  if (selected === "land" && relief?.kind === "river" && item.rivers[relief.index]) {
    const river = item.rivers[relief.index];
    const text = pref.id === "30" && river.name === "紀の川" ?
      "奈良県では吉野川と呼ばれ、和歌山県では紀の川と呼ばれます。和歌山市で紀伊水道に注ぎます。" :
      river.name === item.land ? facts.land[1] : "";
    facts.land = [river.name,text];
  } else if (selected === "land" && relief?.kind === "peak" && item.peaks[relief.index]) {
    const peak = item.peaks[relief.index];
    facts.land = [peak.name, `標高は${peak.height}メートルです。`];
  }
  if (selected === "land" && (!relief || relief.kind === "main") && pref.id === "30") {
    facts.land[1] = "有田川の下流には、日当たりのよい斜面にみかんの段々畑が広がります。";
  }
  const [title, text] = facts[selected];
  $("fact-title").textContent = title;
  $("fact-text").textContent = text;
  $("fact-text").hidden = !text;
  $("explore-fact").hidden = selected === "capital";
  $("industry-stories").hidden = selected !== "industry";
  for (const key of ["capital","land","industry"]) {
    const control = $("discover-"+key);
    control.setAttribute("aria-pressed", String(selected === key));
    control.querySelector("span").hidden = !didOpen(key);
  }
  const canStart = canStartQuiz();
  $("start-quiz").disabled = !canStart;
  const remaining = ["land","industry"].filter(key=>!didOpen(key)).map(key=>key==="land"?"「地形」":"「産業・特産品」");
  const guide = $("quiz-unlock-hint");
  const message = canStart ? "地形と産業・特産品を たしかめたよ。" : remaining.join("と")+"を ひらいてから クイズへ。";
  if (guide.textContent !== message) guide.textContent = message;
}
function renderIndustryStories(pref, stories, active) {
  const cards = $("industry-stories");
  if (cards.dataset.prefecture !== pref.id) {
    cards.dataset.prefecture = pref.id;
    cards.replaceChildren(...stories.map(story => {
      const card = document.createElement("section");
      card.className = "local-story";
      card.dataset.story = story.key;
      const category = document.createElement("p");
      category.className = "story-category";
      category.textContent = story.category;
      const heading = document.createElement("h4");
      const pick = document.createElement("button");
      pick.type = "button";
      pick.className = "story-pick";
      const reading = story.reading && story.reading !== story.name ? `（${story.reading}）` : "";
      pick.textContent = `${story.number}. ${story.name}${reading}`;
      pick.onclick = () => selectMapStory(story.key, false);
      heading.append(pick);
      const pitch = document.createElement("p");
      pitch.textContent = story.intro;
      const source = document.createElement("a");
      source.href = story.source;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = story.source_label;
      card.append(category,heading,pitch,source);
      return card;
    }));
  }
  for (const card of cards.children) {
    const selected = card.dataset.story === active.key;
    card.classList.toggle("active",selected);
    card.querySelector("button").setAttribute("aria-pressed",String(selected));
  }
}
function openFeature(key) {
  if (attempt.phase !== "explore") return;
  wake();
  if (!didOpen(key)) attempt.actions.push({type:"explore",feature:key,at:time()});
  attempt.view = key;
  attempt.relief = null;
  attempt.mapStory = null;
  drawExplore(prefectures.get(attempt.pref));
  diagnostic("feature_opened",{feature:key});
  readCurrent();
  persist();
}
function startQuiz() {
  if (!canStartQuiz()) return;
  attempt.phase = "quiz";
  nextQuestion();
}
function nextQuestion() {
  if (!attempt || attempt.phase !== "quiz") return;
  stopQuizListening();
  const total = menuForVersion(attempt.menu, attempt.content_version).planned_question_count;
  if (attempt.questions.length >= total) { finish("completed"); return; }
  const q = quizQuestions()[attempt.questions.length];
  attempt.questions.push({id:q.id, shown:time(), options:shuffled(["0","1","2"])});
  showQuestion();
  $("quiz-prompt").focus({preventScroll:true});
  readCurrent();
}
function normalizeQuizSpeech(text) {
  return String(text).normalize("NFKC").toLowerCase()
    .replace(/[ァ-ヶ]/g, letter=>String.fromCharCode(letter.charCodeAt(0)-0x60))
    .replace(/[\s\p{P}\p{S}]/gu,"");
}
function choiceVoiceForms(label) {
  const base = label.replace(/[（(][^）)]+[）)]/g,"");
  const notes = [...label.matchAll(/[（(]([^）)]+)[）)]/g)].flatMap(match=>match[1].split(/[、／/]/u));
  return [base, ...notes, label];
}
const QUIZ_SPELLINGS = {
  "根釧台地": ["こんせん台地", "根釧だいち"],
  "りんご": ["林檎"], "みかん": ["蜜柑"], "カキ": ["牡蠣"], "ふぐ": ["河豚"],
  "ねぎ": ["葱"], "たまねぎ": ["玉ねぎ", "玉葱"], "だいこん": ["大根"],
  "なす": ["茄子"], "のり": ["海苔"], "わかめ": ["若布"], "さつまいも": ["薩摩芋"],
};
function parseQuizSpeech(text, question, recorded, pref) {
  let phrase = normalizeQuizSpeech(text);
  const prefix = [pref.name, pref.reading].filter(Boolean).map(normalizeQuizSpeech)
    .flatMap(name=>[name+"は",name+"わ"]).find(name=>phrase.startsWith(name));
  if (prefix) phrase = phrase.slice(prefix.length);
  const matches = recorded.options.filter(key=>{
    const index = Number(key);
    const forms = choiceVoiceForms(question.options[index]);
    forms.push(...(QUIZ_SPELLINGS[forms[0]] || []), ...question.readings[index].split("、"));
    return forms.map(normalizeQuizSpeech).some(form=>form && (phrase===form || phrase===form+"です"));
  });
  return matches.length === 1 ? {key:matches[0]} : {reason:"choice"};
}
function drawQuiz() {
  const question = quizQuestions()[attempt.questions.length-1], recorded = attempt.questions.at(-1);
  const answered = recorded.choice !== undefined;
  const topic = {capital:"県庁所在地", map:"地形", industry:"産業・特産品"}[question.skill];
  $("quiz-name").textContent = topic ? `${info().name} ・ ${topic}` : info().name;
  $("quiz-prompt").textContent = question.prompt;
  $("choices").replaceChildren(...recorded.options.map(key => {
    const item = document.createElement("li");
    item.textContent = question.options[Number(key)];
    if (answered && key === question.correct) item.className = "answer";
    if (answered && recorded.choice === key && key !== question.correct) item.className = "incorrect";
    return item;
  }));
  $("quiz-voice").hidden = answered;
  $("quiz-format").textContent = "選んだ名前を言ってね。「〇〇です」でも答えられるよ。";
  updateQuizMic(QuizRecognition ? "" : "このブラウザーでは音声認識を使えません。音声認識に対応したブラウザーで開いてね。");
  $("quiz-feedback").hidden = !answered;
  if (answered) {
    const correctName = choiceVoiceForms(question.options[Number(question.correct)])[0];
    const result = recorded.choice === question.correct ? "せいかい！" : "答えは" + correctName + "です。";
    $("quiz-feedback").textContent = result + " " + question.explanation;
  }
  $("next").hidden = !answered;
  $("next").textContent = attempt.questions.length === menuForVersion(attempt.menu, attempt.content_version).planned_question_count ? "けっかを 見る" : "つぎの問題";
}
function updateQuizMic(message) {
  $("quiz-voice-status").textContent = message;
  $("quiz-mic").disabled = !QuizRecognition || !!quizListener && !quizListener.started;
  $("quiz-mic").textContent = quizListener?.started ? "聞き取りを終える" :
    quizListener ? "マイクを準備中…" : "🎙 声で答える";
}
function stopQuizListening(message = "") {
  if (!quizListener) return;
  const {recognition,timer} = quizListener;
  quizListener = null;
  clearTimeout(timer);
  try { recognition.abort(); } catch {}
  updateQuizMic(message);
}
function listenForQuizAnswer() {
  if (stage!=="game" || attempt?.phase!=="quiz" || document.hidden || !QuizRecognition) return;
  const recorded = attempt.questions.at(-1);
  if (!recorded || recorded.choice!==undefined) return;
  if (quizListener) {
    if (quizListener.started) {
      try { quizListener.recognition.stop(); } catch {}
    }
    return;
  }
  const question = quizQuestions()[attempt.questions.length-1], pref = info();
  cancelSpeech();
  wake();
  let recognition;
  try { recognition = new QuizRecognition(); }
  catch { updateQuizMic("マイクを開けませんでした。もう一度試してね。"); return; }
  recognition.lang = "ja-JP";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  const listener = {recognition, started:false};
  quizListener = listener;
  const current = () => quizListener===listener && stage==="game" && attempt?.questions.at(-1)===recorded;
  const retry = (message, code) => {
    if (!current()) return;
    diagnostic("speech_answer",{outcome:"retry",code});
    stopQuizListening(message);
  };
  const tryAgain = "聞き取れなかったよ。もう一度「声で答える」を押してね。";
  recognition.onstart = () => {
    if (!current()) return;
    listener.started = true;
    clearTimeout(listener.timer);
    listener.timer = setTimeout(()=>retry(tryAgain,"timeout"),30000);
    updateQuizMic("聞いています。選んだ名前を言ってね。");
  };
  recognition.onresult = event => {
    if (!current()) return;
    const result = event.results[event.resultIndex ?? 0];
    if (!result?.isFinal || !result[0]?.transcript) return;
    const {key,reason} = parseQuizSpeech(result[0].transcript,question,recorded,pref);
    if (key===undefined) {
      retry("選択肢にある名前を、もう一度言ってね。",reason);
      return;
    }
    stopQuizListening();
    diagnostic("speech_answer",{outcome:"accepted"});
    answer(key,recorded);
  };
  recognition.onerror = event => {
    const denied = ["not-allowed","service-not-allowed"].includes(event.error);
    retry(denied ? "マイクの使用を許可してから、もう一度試してね。" :
      event.error==="audio-capture" ? "マイクが使えるか確かめてから、もう一度試してね。" :
      event.error==="network" ? "音声認識の通信に失敗したよ。もう一度試してね。" : tryAgain,event.error);
  };
  recognition.onend = () => retry(tryAgain,"no-result");
  listener.timer = setTimeout(()=>retry("マイクを準備できなかったよ。もう一度試してね。","start-timeout"),15000);
  updateQuizMic("マイクを準備しています。");
  try { recognition.start(); }
  catch { retry("マイクを開けませんでした。もう一度試してね。","start-error"); }
}
function answer(id, recorded) {
  if (attempt?.phase!=="quiz" || attempt.questions.at(-1)!==recorded ||
      recorded.choice!==undefined || !recorded.options.includes(id)) return;
  wake();
  recorded.choice = id;
  recorded.answered = time();
  recorded.input_method = "speech";
  drawQuiz();
  $("next").focus();
  readCurrent();
  persist();
}
function mapPoint(event) {
  const svg = $("map"), matrix = svg.getScreenCTM();
  return matrix ? new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse()) : null;
}
function targetAt(event) {
  const box = $("map").getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) return null;
  const point = mapPoint(event);
  return point ? [...paths].reverse().find(([,path])=>path.isPointInFill(point))?.[0] || null : null;
}
function moveGhost(event) {
  const point = mapPoint(event);
  if (!point) return;
  const [x,y] = prefectures.get(attempt.pref).anchor;
  $("ghost").setAttribute("transform", `translate(${point.x-x} ${point.y-y})`);
  $("ghost").setAttribute("visibility","visible");
}
function finish(status) {
  stopTime();
  attempt.ended = time();
  attempt.status = status;
  if (status === "completed") {
    const total = menuForVersion(attempt.menu, attempt.content_version).planned_question_count;
    const right = attempt.questions.filter(q=>q.choice === "0").length;
    const item = info();
    $("summary").textContent = `${right === total ? "金" : "銀"}メダル　${item.name}　${right} / ${total}問 正解`;
    medalResult = {id:attempt.id,grade:right===total?"gold":"silver",mode:profile?"saving":"local",info:item};
    $("medal-score").textContent = `${item.name}　${right} / ${total}問 正解`;
    diagnostic("round_finished",{state:"completed"});
  }
  cache.history.push(attempt);
  if (profile) cache.queue.push(attempt);
  attempt = null;
  persist();
  sync();
  if (status === "completed") {
    display("result");
    updateMedal();
    $("medal-dialog").showModal();
    readCurrent();
  } else showMenu();
}

const piece = $("piece");
piece.addEventListener("click", event => {
  if (event.detail !== 0 || placed()) return;
  armed = !armed;
  drawQuestion();
  if (armed) $("map").focus();
});
piece.addEventListener("pointerdown", event => {
  if (!event.isPrimary || placed()) return;
  wake();
  drag = {id:event.pointerId, x:event.clientX, y:event.clientY, moved:false};
  piece.setPointerCapture(event.pointerId);
});
piece.addEventListener("pointermove", event => {
  if (!drag || event.pointerId !== drag.id) return;
  if (Math.hypot(event.clientX-drag.x,event.clientY-drag.y)>5) drag.moved = true;
  if (drag.moved) moveGhost(event);
});
piece.addEventListener("pointerup", event => {
  if (!drag || event.pointerId !== drag.id) return;
  const moved = drag.moved;
  drag = null;
  $("ghost").setAttribute("visibility","hidden");
  if (moved) put(targetAt(event));
  else {
    armed = !armed;
    drawQuestion();
    if (armed) $("feedback").textContent = "地図で 場所を えらぼう。";
  }
});
piece.addEventListener("pointercancel", () => { drag=null; $("ghost").setAttribute("visibility","hidden"); });
$("map").addEventListener("click", event => { if (armed && !placed()) put(targetAt(event)); });
$("map").addEventListener("keydown", event => {
  if (placed()) return;
  const directions = {ArrowDown:1, ArrowRight:1, ArrowUp:-1, ArrowLeft:-1};
  if (Object.hasOwn(directions, event.key)) {
    event.preventDefault();
    const list = zoomed ? [...paths.keys()].filter(id=>{
      const [x,y]=prefectures.get(id).anchor, b=$("map").viewBox.baseVal;
      return x>=b.x && x<=b.x+b.width && y>=b.y && y<=b.y+b.height;
    }) : [...paths.keys()];
    if (!list.length) return;
    const old = list.indexOf([...paths.keys()][keyboard]);
    const next = old < 0 ? (directions[event.key]>0 ? 0 : list.length-1) : (old+directions[event.key]+list.length)%list.length;
    keyboard = [...paths.keys()].indexOf(list[next]);
    drawQuestion();
  } else if ((event.key==="Enter" || event.key===" ") && keyboard>=0) {
    event.preventDefault();
    put([...paths.keys()][keyboard]);
  }
});
$("hint").onclick = () => {
  if (placed()) return;
  wake();
  current().actions.push({type:"hint",at:time()});
  drawQuestion();
  persist();
};
$("zoom").onclick = () => {
  if (placed()) return;
  wake();
  zoomed = !zoomed;
  attempt.mapZoomed = zoomed;
  if (zoomed) current().actions.push({type:"zoom",at:time()});
  updateMap(); drawQuestion(); persist();
};
$("age").onchange = () => { cache.age = Number($("age").value); persist(); showMenu(); };
for (const key of ["capital","land","industry"]) $("discover-"+key).onclick = () => openFeature(key);
$("reveal-prefecture").onclick = revealPrefecture;
$("start-quiz").onclick = startQuiz;
$("quiz-mic").onclick = listenForQuizAnswer;
$("next").onclick = nextQuestion;
$("quit").onclick = () => {
  stopTime();
  persist();
  showMenu();
  $("region-heading").focus({preventScroll:true});
};
$("resume").onclick = () => {
  if (!attempt || !canOpenCourse(menus.get(attempt.menu))) return;
  showQuestion();
  readCurrent();
};
$("voice-toggle").onchange = () => {
  autoVoice = $("voice-toggle").checked;
  if (autoVoice) { stopQuizListening(); readCurrent(); } else cancelSpeech();
};
$("medal-retry").onclick = () => { setMedalMode("saving"); sync(); };
$("again").onclick = showMenu;
$("retry").onclick = () => {
  if (profile && hello!=="relink") { if (medalResult) setMedalMode("saving"); sync(); }
  else send("hello");
  updateConnection();
};
$("export").onclick = () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify({version:args.version,build:args.build,records:load("ui-diagnostics") || []},null,2)],{type:"application/json"}));
  const a = document.createElement("a"); a.href = url; a.download = "geography-ui-network-log.json"; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function pausePage() {
  stopQuizListening();
  stopTime();
  persist();
  cancelSpeech();
}
document.addEventListener("visibilitychange", () => { if (document.hidden) pausePage(); else wake(); });
window.addEventListener("pagehide", pausePage);
window.addEventListener("message", receive);
new ResizeObserver(() => post("setFrameHeight",{height:Math.ceil(document.body.getBoundingClientRect().height)+1})).observe(document.body);
post("componentReady",{apiVersion:1});
</script>
</body>
</html>
'''

HUB_URL = "https://chokomana-hkgx4uyxxezjtr2sj35jwj.streamlit.app/"


def setting(name, fallback=""):
    try:
        return str(st.secrets.get(name, os.environ.get(name, fallback))).strip()
    except FileNotFoundError:
        return os.environ.get(name, fallback)


def https(url):
    parsed = urlsplit(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username


def request(path, body):
    base = setting("SUPABASE_URL").rstrip("/")
    key = setting("SUPABASE_SERVICE_ROLE_KEY") or setting("SUPABASE_SECRET_KEY")
    headers = {"apikey": key, "Content-Type": "application/json"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"
    req = Request(f"{base}/rest/v1/{path}", json.dumps(body).encode(), headers, method="POST")
    with urlopen(req, timeout=11) as response:
        data = response.read()
        return json.loads(data) if data else None


@st.cache_data(ttl=3600, show_spinner=False)
def publish_catalog(base, catalog_revision):
    rows = list(catalog())
    for start in range(0, len(rows), 200):
        batch = rows[start:start+200]
        result = request("rpc/cm_geography_publish_catalog_v1", {"p_rows": batch})
        if not isinstance(result, dict) or result.get("received") != len(batch):
            raise RuntimeError("missing catalog confirmation")


def database_error(error):
    fields = {"http_status": error.code}
    try:
        problem = json.loads(error.read(8192))
    except (ValueError, OSError):
        return fields, False
    if not isinstance(problem, dict):
        return fields, False
    db_code = problem.get("code")
    if isinstance(db_code, str) and re.fullmatch(r"[A-Z0-9]{5,8}", db_code):
        fields["db_code"] = db_code
    message = problem.get("message")
    for label, description in (
        ("event_write", "geography event write failed"),
        ("medal_write", "geography medal write failed"),
        ("unverified_profile", "unverified profile"),
    ):
        if message == description:
            fields["failure"] = label
            break
    if fields.get("failure") in {"event_write", "medal_write"}:
        try:
            detail = json.loads(problem.get("details") or "{}")
        except (TypeError, ValueError):
            detail = None
        if isinstance(detail, dict):
            for key in ("column", "constraint"):
                value = detail.get(key)
                if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,62}", value):
                    fields[key] = value
    return fields, db_code == "42501" and message == "unverified profile"


def process(message, state, configured):
    ident = str(UUID(message["id"]))
    if state.get("ack", {}).get("id") == ident:
        return False
    result = {"id": ident, "status": "retry"}
    stage = "connection"
    try:
        if message["action"] == "hello":
            device = message["device"]
            if not re.fullmatch(r"[0-9a-f]{64}", device):
                raise ValueError("invalid device")
            if not configured:
                result["status"] = "local"
            else:
                proof = hashlib.sha256(("chokomana:geography:" + device).encode()).hexdigest()
                ticket = state.get("ticket")
                data = request("rpc/cm_geography_claim_v1", {
                    "p_device_hash": proof,
                    "p_ticket_hash": hashlib.sha256(ticket.encode()).hexdigest() if ticket else None,
                })
                profile = data.get("profile_id")
                if profile:
                    state["profile"] = str(UUID(profile))
                    state["proof"] = proof
                    state["assignment"] = data.get("assignment")
                    age = data.get("age")
                    state["age"] = age if type(age) is int and 1 <= age <= 100 else None
                    result["status"] = "linked"
                else:
                    state.pop("profile", None)
                    state.pop("proof", None)
                    state.pop("assignment", None)
                    state.pop("age", None)
                    result["status"] = "invalid_ticket" if ticket else "local"
                state.pop("ticket", None)
                if "cm_launch" in st.query_params:
                    del st.query_params["cm_launch"]
        elif message["action"] == "sync":
            profile = state["profile"]
            if profile != message.get("profile"):
                raise PermissionError("invalid owner")
            raw = message["attempt"]
            assignment = None
            if raw.get("assignment"):
                stage = "assignment"
                binding = request("rpc/cm_geography_assignment_v1", {
                    "p_device_hash": state["proof"], "p_profile": profile,
                    "p_plan_item_id": str(UUID(raw["assignment"])),
                })
                assignment = binding or None
            stage = "record_validation"
            events, medal = build_records(raw, profile, assignment)
            stage = "record_save"
            saved = request("rpc/cm_geography_save_v1", {
                "p_device_hash": state["proof"], "p_profile": profile,
                "p_events": events, "p_medal": medal,
            })
            if not saved or saved.get("attempt_id") != raw["id"]:
                raise RuntimeError("missing save confirmation")
            result.update(status="saved", attempt_id=saved["attempt_id"], medal_saved=medal is not None)
        else:
            raise ValueError("invalid action")
    except (ValueError, TypeError, KeyError, PermissionError, IndexError):
        result["status"] = "invalid"
    except HTTPError as error:
        fields, relink = database_error(error)
        result.update(fields)
        logging.getLogger(__name__).warning("Geography %s failed: %s", stage, fields)
        if relink:
            result["status"] = "relink"
    except (OSError, RuntimeError):
        logging.getLogger(__name__).warning("Geography persistence unavailable")
    result["stage"] = stage
    state["ack"] = result
    return True


@st.cache_resource(show_spinner=False)
def frontend_folder(page):
    folder = TemporaryDirectory(prefix="chokomana_geography_")
    (Path(folder.name) / "index.html").write_text(page, encoding="utf-8")
    return folder


def cm_graduation_snapshot(rows, profile, source):
    if not isinstance(rows, list) or len(rows) > 1:
        raise ValueError('invalid graduation state')
    if not rows:
        return {}
    row = rows[0]
    if str(row.get('profile_id')) != str(profile) or row.get('source_app') != source:
        raise ValueError('graduation owner mismatch')
    items = row.get('items')
    if not isinstance(items, dict):
        raise ValueError('invalid graduation items')
    return {key: item for key, item in items.items()
            if key.startswith(('unit:', 'question:')) and isinstance(item, dict)}


def cm_poll_graduation(st, state, profile, source, read_rows):
    # The profile comes from the server-verified link, never the browser message.
    if state.get('_cm_graduation_owner') != profile:
        state['_cm_graduation_owner'] = profile
        state['_cm_graduation_units'] = []
        state.pop('_cm_graduation_checked', None)
    if not profile:
        return
    import time
    if time.monotonic() - state.get('_cm_graduation_checked', -15) < 14:
        return
    state['_cm_graduation_checked'] = time.monotonic()
    try:
        items = cm_graduation_snapshot(read_rows(), profile, source)
    except Exception as exc:
        import logging
        logging.getLogger('chokomana_graduation').warning('%s graduation read failed (%s)', source, type(exc).__name__)
        return
    units = sorted(key[5:] for key, item in items.items()
                   if key.startswith('unit:') and isinstance(item.get('record'), dict))
    if units != state['_cm_graduation_units']:
        state['_cm_graduation_units'] = units
        st.rerun()


def cm_geography_graduation_rows(profile):
    base = setting('SUPABASE_URL').rstrip('/')
    key = setting('SUPABASE_SERVICE_ROLE_KEY') or setting('SUPABASE_SECRET_KEY')
    params = urlencode({'profile_id': 'eq.' + profile, 'source_app': 'eq.geography',
                        'select': 'profile_id,source_app,items', 'limit': '1'})
    headers = {'apikey': key}
    if not key.startswith('sb_secret_'):
        headers['Authorization'] = 'Bearer ' + key
    with urlopen(Request(base + '/rest/v1/chokomana_graduation_states?' + params, headers=headers), timeout=8) as response:
        return json.load(response)


def hub_return_url():
    hub = setting("CHOKOMANA_HOME_URL", HUB_URL)
    parts = urlsplit(hub if https(hub) else HUB_URL)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key != "cm_plan_return"]
    query.append(("cm_plan_return", "1"))
    return urlunsplit(parts._replace(query=urlencode(query)))


def main():
    st.set_page_config(page_title="ちょこまな｜しゃかい・ちり", page_icon="🗾", layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown("<style>.block-container{max-width:1050px;padding:1.4rem .8rem}"
                "header[data-testid='stHeader']{background:transparent}</style>", unsafe_allow_html=True)
    state = st.session_state.setdefault("geography", {})
    ticket = st.query_params.get("cm_launch")
    if ticket and re.fullmatch(r"[A-Za-z0-9_-]{20,128}", ticket):
        mark = hashlib.sha256(ticket.encode()).hexdigest()
        if mark != state.get("launch"):
            state.clear()
            state.update(ticket=ticket, launch=mark)
    base = setting("SUPABASE_URL")
    configured = https(base) and bool(setting("SUPABASE_SERVICE_ROLE_KEY") or setting("SUPABASE_SECRET_KEY"))
    if configured and state.get("catalog_checked") != CATALOG_REVISION:
        state["catalog_checked"] = CATALOG_REVISION
        start = perf_counter()
        outcome, fields = "saved", {}
        try:
            publish_catalog(base, CATALOG_REVISION)
        except HTTPError as error:
            fields, _ = database_error(error)
            outcome = "retry"
        except (ValueError, OSError, RuntimeError):
            outcome = "retry"
        state["catalog_status"] = dict(operation="catalog", stage="catalog", outcome=outcome,
                                       code=fields.pop("http_status", None),
                                       ms=round((perf_counter()-start)*1000), **fields)
    st.link_button("← ちょこまなへ", hub_return_url())
    build = hashlib.sha256(FRONTEND_HTML.encode("utf-8")).hexdigest()[:16]
    component = declare_component(f"chokomana_geography_{build}", path=frontend_folder(FRONTEND_HTML).name)
    profile = state.get('profile') if configured else None
    @st.fragment(run_every=15)
    def check_graduation():
        cm_poll_graduation(st, state, profile, 'geography', lambda: cm_geography_graduation_rows(profile))
    check_graduation()
    message = component(graduated_units=state.get('_cm_graduation_units', []), map=MAP, discovery=DISCOVERY, menus=list(MENUS.values()),
        version=VERSION, previous_version=TWO_QUESTION_VERSION, previous_menus=list(TWO_QUESTION_MENUS.values()),
        build=build, age=state.get("age"),
        configured=configured, profile=state.get("profile"),
        plan_launch=bool(state.get("launch")), assignment=state.get("assignment"), ack=state.get("ack"), catalog_status=state.get("catalog_status"),
        key="geography_" + state.get("launch", "standalone")[:16], default=None)
    if isinstance(message, dict):
        try:
            if process(message, state, configured):
                st.rerun()
        except (ValueError, KeyError, TypeError):
            return


if __name__ == "__main__":
    main()

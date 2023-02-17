
from datetime import datetime, date, timedelta
import pytz
from tzlocal import get_localzone
import shaystack
from shaystack import Ref
from shaystack.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
import requests

mime_type = shaystack.MODE_ZINC
grid = shaystack.Grid(columns={'id': {}, 'point' : {}})
grid.append({"id": Ref("@p:stm_campus:r:1f5c5828-728bdb32"), "point" : "curVal"})
headers = {"Content-Type" : mime_type, "Accept" : mime_type}
datas = shaystack.dump(grid, mode=mime_type)
print("DATA : ", datas)
url ="https://internal-apis.nrel.gov/intelligentcampus/stm_campus/read"
tmp = requests.post(url = url, data=datas, headers=headers)
print(tmp.text)
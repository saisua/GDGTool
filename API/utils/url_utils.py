import re

url_re = re.compile(r"^((https?:\/\/)?\w+\.(\.?\w{2,})+\S*|about:\w+(#\w+)?)$")
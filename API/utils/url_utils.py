import re

url_re = re.compile(r"^((https?:\/\/)?\w+\.(\.?\w{2,})+\S*|about:\w+(#\w+)?)$")

def check_valid_url(url: str) -> None:
    assert isinstance(url, str), f"URL \"{url}\" must be a string"
    assert url_re.match(url), f"URL \"{url}\" is not valid"
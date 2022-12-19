import os
import sys
import re

env_re = re.compile(r"^\s*(\w+)\s*=\s*([^\s#][^\n#]*)", re.MULTILINE)

with open("./.env", 'r') as env_file:
    env_str = env_file.read()

env_vars = {**dict(env_re.findall(env_str)), **os.environ}
print(env_re.findall(env_str), env_str, sep='\n')

print("Importing spacy...")
import spacy
print("[+] Done (Spacy import)")

spacy_model = env_vars["SCRAPER_SPACY_MODEL"]
print(f"Downloading spacy model \"{spacy_model}\"...")
spacy.cli.download(spacy_model)
print(f"[+] Done ({spacy_model} download)")

print("Importing nltk...")
import nltk
print("[+] Done (nltk import)")

print("Downloading nltk model \"wordnet\"...")
nltk.download("wordnet")
print("[+] Done (wordnet download)")

print("Downloading nltk model \"omw-1.4\"...")
nltk.download("omw-1.4")
print("[+] Done (omw-1.4 download)")

print("Importing coreferee...")
import coreferee
print("[+] Done (coreferee import)")

print("Downloading coreferee model...")
spacy.util.run_command(
    " ".join((
        sys.executable,
        "-m pip install",
        ''.join((
            "https://github.com/msg-systems/coreferee/raw/master/models",
            "/",
            coreferee.manager.COMMON_MODELS_PACKAGE_NAMEPART,
            spacy_model.split('_', 1)[0],
            ".zip"
        )),
    ))
)
print("[+] Done (coreferee model download)")
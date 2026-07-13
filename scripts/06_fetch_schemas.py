"""
Download the PBIP/PBIR JSON schemas (plus every transitively $ref'd schema)
into GlobalHealthEquity/_validation/schemas so validate.py can run offline.
Writes urls.json mapping each local file to the URIs it must be registered
under (its fetch URL and its internal $id, which sometimes differ).
"""
import json
import os
import re

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "GlobalHealthEquity", "_validation", "schemas")
os.makedirs(OUT, exist_ok=True)

ROOTS = [
    "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.1.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
]


def url_to_fname(url):
    return url.split("json-schemas/")[1].replace("/", "__")


def resolve(base_url, ref):
    ref = ref.split("#")[0]
    if not ref:
        return None
    if ref.startswith("http"):
        return ref
    base_parts = base_url.split("/")[:-1]
    for part in ref.split("/"):
        if part == "..":
            base_parts.pop()
        elif part != ".":
            base_parts.append(part)
    return "/".join(base_parts)


seen, queue, mapping = {}, list(ROOTS), {}
while queue:
    url = queue.pop()
    if url in seen:
        continue
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    doc = r.json()
    fname = url_to_fname(url)
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    uris = {url}
    if "$id" in doc:
        uris.add(doc["$id"])
    mapping[fname] = sorted(uris)
    seen[url] = fname
    for ref in set(re.findall(r'"\$ref"\s*:\s*"([^"#]+)', json.dumps(doc))):
        target = resolve(url, ref)
        if target and target not in seen:
            queue.append(target)
    print("fetched", fname)

with open(os.path.join(OUT, "urls.json"), "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=1)
print(f"\n{len(mapping)} schemas saved to {os.path.abspath(OUT)}")

"""
Validation for the GlobalHealthEquity PBIP project. Run from this folder:

    python validate.py

Checks:
 1. Every JSON-based file (.json, .pbip, .pbir, .pbism, .platform) parses.
 2. Every file that declares a $schema validates against the schema copy in
    _validation/schemas (fetched from developer.microsoft.com).
 3. The TMDL model is parsed (tables / columns / calculated columns / measures)
    and every visual queryRef, field binding, filter field and sort field is
    cross-checked against it (case-sensitive).
 4. sortByColumn targets exist; partition source columns match the real CSV
    headers at the DataPath default; pages.json page names match folders;
    visual names are unique; positions fit the 1280x720 canvas.

Requires: pip install jsonschema  (referencing comes with jsonschema>=4.18)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SM_DEF = os.path.join(HERE, "GlobalHealthEquity.SemanticModel", "definition")
RPT_DEF = os.path.join(HERE, "GlobalHealthEquity.Report", "definition")
SCHEMA_DIR = os.path.join(HERE, "_validation", "schemas")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- 1. JSON parse
json_files = []
for root, _, files in os.walk(HERE):
    if "_validation" in root:
        continue
    for f in files:
        if f.endswith((".json", ".pbip", ".pbir", ".pbism", ".platform")):
            json_files.append(os.path.join(root, f))

docs = {}
for path in sorted(json_files):
    rel = os.path.relpath(path, HERE)
    try:
        with open(path, encoding="utf-8") as fh:
            docs[rel] = json.load(fh)
    except Exception as e:
        err(f"JSON PARSE {rel}: {e}")
print(f"[1] parsed {len(docs)}/{len(json_files)} JSON files")

# ---------------------------------------------------------------- 2. schemas
try:
    import jsonschema
    from referencing import Registry, Resource

    from referencing.jsonschema import DRAFT7

    with open(os.path.join(SCHEMA_DIR, "urls.json"), encoding="utf-8") as fh:
        url_map = json.load(fh)
    resources = []
    for fname, uris in url_map.items():
        with open(os.path.join(SCHEMA_DIR, fname), encoding="utf-8") as fh:
            schema_doc = json.load(fh)
        res = Resource(contents=schema_doc, specification=DRAFT7)
        for uri in uris:
            resources.append((uri, res))
    registry = Registry().with_resources(resources)

    n_validated = 0
    for rel, doc in docs.items():
        schema_url = doc.get("$schema") if isinstance(doc, dict) else None
        if not schema_url:
            continue
        match = [u for fname, uris in url_map.items() for u in uris if u == schema_url]
        if not match:
            warn(f"SCHEMA MISSING for {rel}: {schema_url} not in _validation/schemas")
            continue
        with open(os.path.join(
                SCHEMA_DIR,
                [f for f, uris in url_map.items() if schema_url in uris][0]),
                encoding="utf-8") as fh:
            schema_doc = json.load(fh)
        validator = jsonschema.Draft7Validator(schema_doc, registry=registry)
        for e in validator.iter_errors(doc):
            err(f"SCHEMA {rel}: {'/'.join(str(p) for p in e.absolute_path)}: {e.message[:200]}")
        n_validated += 1
    print(f"[2] schema-validated {n_validated} files")
except ImportError:
    warn("jsonschema/referencing not installed - schema validation skipped")

# ---------------------------------------------------------------- 3. TMDL model
tables = {}   # name -> {"columns": set, "measures": set, "sort_targets": []}
for f in os.listdir(os.path.join(SM_DEF, "tables")):
    text = open(os.path.join(SM_DEF, "tables", f), encoding="utf-8").read()
    tname_m = re.match(r"table (?:'([^']+)'|(\S+))", text)
    tname = tname_m.group(1) or tname_m.group(2)
    cols = set(re.findall(r"^\tcolumn (?:'([^']+)'|([^\s=]+))", text, re.M))
    cols = {a or b for a, b in cols}
    meas = set(re.findall(r"^\tmeasure (?:'([^']+)'|([^\s=]+))", text, re.M))
    meas = {a or b for a, b in meas}
    sorts = [a or b for a, b in
             re.findall(r"sortByColumn: (?:'([^']+)'|(\S+))", text)]
    parts = re.findall(r"^\tpartition (?:'([^']+)'|(\S+))", text, re.M)
    tables[tname] = {"columns": cols, "measures": meas, "sorts": sorts,
                     "text": text, "partitions": [a or b for a, b in parts]}
print(f"[3] TMDL parsed: " + ", ".join(
    f"{t}({len(v['columns'])}c/{len(v['measures'])}m)" for t, v in tables.items()))

for tname, t in tables.items():
    for s in t["sorts"]:
        if s not in t["columns"]:
            err(f"TMDL {tname}: sortByColumn '{s}' does not exist")
    if not t["partitions"]:
        err(f"TMDL {tname}: no partition defined")

# DataPath default + CSV header check against sourceColumn lists
expr_text = open(os.path.join(SM_DEF, "expressions.tmdl"), encoding="utf-8").read()
dp_m = re.search(r'expression DataPath = "([^"]+)"', expr_text)
if not dp_m:
    err("expressions.tmdl: DataPath parameter not found")
else:
    data_path = dp_m.group(1)
    for tname, t in tables.items():
        csv_m = re.search(r'DataPath & "\\\\?([^"]+\.csv)"', t["text"])
        if not csv_m:
            err(f"TMDL {tname}: partition does not reference DataPath")
            continue
        csv_file = os.path.join(data_path, csv_m.group(1).lstrip("\\"))
        if not os.path.exists(csv_file):
            warn(f"TMDL {tname}: CSV not found at default DataPath: {csv_file}")
            continue
        header = open(csv_file, encoding="utf-8").readline().strip().split(",")
        src_cols = re.findall(r"sourceColumn: (\S+)", t["text"])
        for c in src_cols:
            if c not in header:
                err(f"TMDL {tname}: sourceColumn '{c}' not in {os.path.basename(csv_file)} header {header}")

# ---------------------------------------------------------------- 4. visuals
def iter_field_refs(node, alias_map):
    """Yield (entity, property, kind) for every Column/Measure reference."""
    if isinstance(node, dict):
        for kind in ("Column", "Measure"):
            if kind in node and isinstance(node[kind], dict):
                ref = node[kind]
                srcref = ref.get("Expression", {}).get("SourceRef", {})
                entity = srcref.get("Entity") or alias_map.get(srcref.get("Source"))
                prop = ref.get("Property")
                if entity and prop:
                    yield entity, prop, kind
        for v in node.values():
            yield from iter_field_refs(v, alias_map)
    elif isinstance(node, list):
        for v in node:
            yield from iter_field_refs(v, alias_map)


def collect_aliases(node, alias_map):
    if isinstance(node, dict):
        if "From" in node and isinstance(node["From"], list):
            for f in node["From"]:
                if isinstance(f, dict) and "Name" in f and "Entity" in f:
                    alias_map[f["Name"]] = f["Entity"]
        for v in node.values():
            collect_aliases(v, alias_map)
    elif isinstance(node, list):
        for v in node:
            collect_aliases(v, alias_map)


visual_docs = {rel: d for rel, d in docs.items()
               if rel.replace("\\", "/").endswith("/visual.json")}
names = {}
n_refs = 0
for rel, v in visual_docs.items():
    name = v.get("name")
    if name in names:
        err(f"{rel}: duplicate visual name '{name}' (also {names[name]})")
    names[name] = rel

    pos = v.get("position", {})
    if pos.get("x", 0) + pos.get("width", 0) > 1280 or pos.get("y", 0) + pos.get("height", 0) > 720:
        warn(f"{rel}: visual extends beyond 1280x720 canvas")

    alias_map = {}
    collect_aliases(v, alias_map)
    for entity, prop, kind in iter_field_refs(v, alias_map):
        n_refs += 1
        if entity not in tables:
            err(f"{rel}: unknown table '{entity}'")
        elif kind == "Column" and prop not in tables[entity]["columns"]:
            err(f"{rel}: column '{entity}'[{prop}] not in model")
        elif kind == "Measure" and prop not in tables[entity]["measures"]:
            err(f"{rel}: measure '{entity}'[{prop}] not in model")

    # queryRef strings must be "<table>.<field>" with both parts real
    qstate = v.get("visual", {}).get("query", {}).get("queryState", {})
    for role, bucket in qstate.items():
        for p in bucket.get("projections", []):
            qref = p.get("queryRef", "")
            t, _, fld = qref.partition(".")
            if t not in tables or (fld not in tables[t]["columns"]
                                   and fld not in tables[t]["measures"]):
                err(f"{rel}: queryRef '{qref}' (role {role}) not found in model")

print(f"[4] {len(visual_docs)} visuals, {n_refs} field references checked")

# pages.json cross-check
pages_meta = docs.get(os.path.join("GlobalHealthEquity.Report", "definition", "pages", "pages.json"))
page_dirs = [d for d in os.listdir(os.path.join(RPT_DEF, "pages"))
             if os.path.isdir(os.path.join(RPT_DEF, "pages", d))]
if pages_meta:
    for p in pages_meta.get("pageOrder", []):
        if p not in page_dirs:
            err(f"pages.json: pageOrder entry '{p}' has no folder")
    if pages_meta.get("activePageName") not in page_dirs:
        err("pages.json: activePageName has no folder")

# ---------------------------------------------------------------- result
print()
for w in warnings:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print(f"\n{'FAILED: ' + str(len(errors)) + ' error(s)' if errors else 'ALL CHECKS PASSED'}"
      f" ({len(warnings)} warning(s))")
sys.exit(1 if errors else 0)

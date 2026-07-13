"""
Generate the GlobalHealthEquity Power BI project (PBIP + TMDL + PBIR).

Output tree (created under ../GlobalHealthEquity/):
  GlobalHealthEquity.pbip
  GlobalHealthEquity.SemanticModel/  (.platform, definition.pbism, definition/*.tmdl)
  GlobalHealthEquity.Report/         (.platform, definition.pbir, definition/**.json)

Schema versions match the files fetched from developer.microsoft.com (see
GlobalHealthEquity/_validation/schemas); validate.py checks every JSON file
against them and cross-checks all queryRefs against the TMDL model.
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PRJ = os.path.join(ROOT, "GlobalHealthEquity")
SM = os.path.join(PRJ, "GlobalHealthEquity.SemanticModel")
RPT = os.path.join(PRJ, "GlobalHealthEquity.Report")

DATA_PATH_DEFAULT = os.path.join(ROOT, "data", "clean")

BASE = "https://developer.microsoft.com/json-schemas"
SCHEMAS = {
    "pbip": f"{BASE}/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "platform": f"{BASE}/fabric/gitIntegration/platformProperties/2.1.0/schema.json",
    "pbism": f"{BASE}/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "pbir": f"{BASE}/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "report": f"{BASE}/fabric/item/report/definition/report/3.0.0/schema.json",
    "pagesMetadata": f"{BASE}/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "page": f"{BASE}/fabric/item/report/definition/page/2.1.0/schema.json",
    "visualContainer": f"{BASE}/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "versionMetadata": f"{BASE}/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
}


def gid():
    return str(uuid.uuid4())


def vid():
    return uuid.uuid4().hex[:20]


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print("json ", os.path.relpath(path, PRJ))


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("text ", os.path.relpath(path, PRJ))


# ============================================================ semantic model
M_TYPES = {"string": "type text", "int64": "Int64.Type", "double": "type number"}

TABLES = {
    "country_year_panel": {
        "csv": "country_year_panel.csv",
        "columns": [
            ("iso3c", "string"), ("country", "string"), ("region", "string"),
            ("income_group", "string"), ("year", "int64"),
            ("gdp_per_capita_usd", "double"), ("health_exp_pct_gdp", "double"),
            ("health_exp_per_capita_usd", "double"), ("under5_mortality_per_1000", "double"),
        ],
        "measures": [
            ("Avg Mortality", "AVERAGE(country_year_panel[under5_mortality_per_1000])", "0.0"),
            ("Avg Health Spend Pct", "AVERAGE(country_year_panel[health_exp_pct_gdp])", "0.0"),
            ("Avg GDP per Capita", "AVERAGE(country_year_panel[gdp_per_capita_usd])", "#,0"),
            ("Countries", "DISTINCTCOUNT(country_year_panel[country])", "#,0"),
        ],
    },
    "country_latest": {
        "csv": "country_latest.csv",
        "columns": [
            ("iso3c", "string"), ("country", "string"), ("region", "string"),
            ("income_group", "string"), ("latest_year", "int64"),
            ("gdp_per_capita_usd", "double"), ("health_exp_pct_gdp", "double"),
            ("health_exp_per_capita_usd", "double"), ("under5_mortality_per_1000", "double"),
        ],
        "measures": [
            ("Avg Mortality 2023", "AVERAGE(country_latest[under5_mortality_per_1000])", "0.0"),
            ("Countries 2023", "DISTINCTCOUNT(country_latest[country])", "#,0"),
            ("GDP per Capita 2023", "AVERAGE(country_latest[gdp_per_capita_usd])", "#,0"),
            ("Health Spend per Capita 2023", "AVERAGE(country_latest[health_exp_per_capita_usd])", "#,0"),
        ],
    },
    "region_year_summary": {
        "csv": "region_year_summary.csv",
        "columns": [
            ("region", "string"), ("year", "int64"),
            ("gdp_per_capita_usd", "double"), ("health_exp_pct_gdp", "double"),
            ("health_exp_per_capita_usd", "double"), ("under5_mortality_per_1000", "double"),
            ("n_countries", "int64"),
        ],
        "measures": [],
    },
    "income_year_summary": {
        "csv": "income_year_summary.csv",
        "columns": [
            ("income_group", "string"), ("year", "int64"),
            ("gdp_per_capita_usd", "double"), ("health_exp_pct_gdp", "double"),
            ("health_exp_per_capita_usd", "double"), ("under5_mortality_per_1000", "double"),
        ],
        "measures": [],
    },
}

BAND_DAX = ('SWITCH(TRUE(), [under5_mortality_per_1000] < 10, "0-10", '
            '[under5_mortality_per_1000] < 25, "10-25", '
            '[under5_mortality_per_1000] < 50, "25-50", '
            '[under5_mortality_per_1000] < 75, "50-75", "75+")')
BAND_ORDER_DAX = ('SWITCH(TRUE(), [under5_mortality_per_1000] < 10, 1, '
                  '[under5_mortality_per_1000] < 25, 2, '
                  '[under5_mortality_per_1000] < 50, 3, '
                  '[under5_mortality_per_1000] < 75, 4, 5)')


def table_tmdl(name, spec):
    L = [f"table {name}", f"\tlineageTag: {gid()}", ""]
    for mname, dax, fmt in spec["measures"]:
        L += [f"\tmeasure '{mname}' = {dax}",
              f"\t\tformatString: {fmt}",
              f"\t\tlineageTag: {gid()}", ""]
    for cname, dtype in spec["columns"]:
        L.append(f"\tcolumn {cname}")
        L.append(f"\t\tdataType: {dtype}")
        if dtype == "int64":
            L.append("\t\tformatString: 0")
        if cname == "country":
            L.append("\t\tdataCategory: Country")
        L += [f"\t\tlineageTag: {gid()}",
              "\t\tsummarizeBy: none",
              f"\t\tsourceColumn: {cname}", "",
              "\t\tannotation SummarizationSetBy = Automatic", ""]
    if name == "country_latest":
        L += [f"\tcolumn 'Mortality Band' = {BAND_DAX}",
              "\t\tdataType: string",
              f"\t\tlineageTag: {gid()}",
              "\t\tsummarizeBy: none",
              "\t\tsortByColumn: 'Mortality Band Order'", "",
              "\t\tannotation SummarizationSetBy = Automatic", "",
              f"\tcolumn 'Mortality Band Order' = {BAND_ORDER_DAX}",
              "\t\tdataType: int64",
              "\t\tformatString: 0",
              "\t\tisHidden",
              f"\t\tlineageTag: {gid()}",
              "\t\tsummarizeBy: none", "",
              "\t\tannotation SummarizationSetBy = Automatic", ""]
    ncols = len(spec["columns"])
    types = ", ".join('{"%s", %s}' % (c, M_TYPES[t]) for c, t in spec["columns"])
    L += [f"\tpartition {name} = m",
          "\t\tmode: import",
          "\t\tsource =",
          "\t\t\t\tlet",
          f'\t\t\t\t    Source = Csv.Document(File.Contents(DataPath & "\\{spec["csv"]}"), '
          f'[Delimiter=",", Columns={ncols}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          '\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
          '\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{%s})' % types,
          "\t\t\t\tin",
          '\t\t\t\t    #"Changed Type"', "",
          "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(L)


for tname, tspec in TABLES.items():
    write_text(os.path.join(SM, "definition", "tables", f"{tname}.tmdl"),
               table_tmdl(tname, tspec))

write_text(os.path.join(SM, "definition", "database.tmdl"),
           "database\n\tcompatibilityLevel: 1601\n")

model_lines = ["model Model",
               "\tculture: en-US",
               "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
               "\tsourceQueryCulture: en-US",
               "\tdataAccessOptions",
               "\t\tlegacyRedirects",
               "\t\treturnErrorValuesAsNull", "",
               "annotation __PBI_TimeIntelligenceEnabled = 0", ""]
model_lines += [f"ref table {t}" for t in TABLES] + [""]
write_text(os.path.join(SM, "definition", "model.tmdl"), "\n".join(model_lines))

write_text(
    os.path.join(SM, "definition", "expressions.tmdl"),
    f'expression DataPath = "{DATA_PATH_DEFAULT}" '
    "meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]\n"
    f"\tlineageTag: {gid()}\n\n"
    "\tannotation PBI_ResultType = Text\n")

write_json(os.path.join(SM, "definition.pbism"),
           {"$schema": SCHEMAS["pbism"], "version": "4.0", "settings": {}})
write_json(os.path.join(SM, ".platform"),
           {"$schema": SCHEMAS["platform"],
            "metadata": {"type": "SemanticModel", "displayName": "GlobalHealthEquity"},
            "config": {"version": "2.0", "logicalId": gid()}})

# ============================================================ report helpers
def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas(entity, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(field, entity, prop):
    return {"field": field, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}


def bucket(*projections):
    return {"projections": list(projections)}


def year_filter(entity, prop, value):
    return {"filters": [{
        "name": vid(),
        "field": col(entity, prop),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                                            "Property": prop}}],
                "Values": [[{"Literal": {"Value": f"{value}L"}}]],
            }}}],
        },
    }]}


def visual(vtype, pos, query_state=None, sort=None, objects=None,
           filter_config=None, z=0):
    v = {"$schema": SCHEMAS["visualContainer"],
         "name": vid(),
         "position": {"x": pos[0], "y": pos[1], "z": z,
                      "width": pos[2], "height": pos[3]},
         "visual": {"visualType": vtype}}
    if query_state:
        q = {"queryState": query_state}
        if sort:
            q["sortDefinition"] = sort
        v["visual"]["query"] = q
    if objects:
        v["visual"]["objects"] = objects
    v["visual"]["drillFilterOtherVisuals"] = True
    if filter_config:
        v["filterConfig"] = filter_config
    return v


PANEL, LATEST = "country_year_panel", "country_latest"

# ---- Page 1: KPI Overview ---------------------------------------------------
p1 = []
card_measures = ["Avg Mortality", "Avg Health Spend Pct", "Avg GDP per Capita", "Countries"]
for i, m in enumerate(card_measures):
    p1.append(visual("card", (210 + i * 266, 12, 256, 96),
                     {"Values": bucket(proj(meas(PANEL, m), PANEL, m))}, z=i))
for i, (scol, h, y) in enumerate([("year", 200, 12), ("region", 240, 222),
                                  ("income_group", 236, 472)]):
    p1.append(visual("slicer", (12, y, 186, h),
                     {"Values": bucket(proj(col(PANEL, scol), PANEL, scol))}, z=4 + i))
p1.append(visual(
    "lineChart", (210, 120, 1058, 300),
    {"Category": bucket(proj(col(PANEL, "year"), PANEL, "year")),
     "Series": bucket(proj(col(PANEL, "income_group"), PANEL, "income_group")),
     "Y": bucket(proj(meas(PANEL, "Avg Mortality"), PANEL, "Avg Mortality"))},
    sort={"sort": [{"field": col(PANEL, "year"), "direction": "Ascending"}],
          "isDefaultSort": True}, z=7))
p1.append(visual(
    "barChart", (210, 432, 1058, 276),
    {"Category": bucket(proj(col(PANEL, "region"), PANEL, "region")),
     "Y": bucket(proj(meas(PANEL, "Avg Mortality"), PANEL, "Avg Mortality"))},
    sort={"sort": [{"field": meas(PANEL, "Avg Mortality"), "direction": "Descending"}],
          "isDefaultSort": True},
    filter_config=year_filter(PANEL, "year", 2023), z=8))

# ---- Page 2: Geography & Distribution ---------------------------------------
p2 = [
    visual("filledMap", (12, 12, 770, 696),
           {"Category": bucket(proj(col(LATEST, "country"), LATEST, "country")),
            "Gradient": bucket(proj(meas(LATEST, "Avg Mortality 2023"),
                                    LATEST, "Avg Mortality 2023"))}, z=0),
    visual("columnChart", (794, 12, 474, 696),
           {"Category": bucket(proj(col(LATEST, "Mortality Band"),
                                    LATEST, "Mortality Band")),
            "Y": bucket(proj(meas(LATEST, "Countries 2023"), LATEST, "Countries 2023"))},
           sort={"sort": [{"field": col(LATEST, "Mortality Band"),
                           "direction": "Ascending"}], "isDefaultSort": True}, z=1),
]

# ---- Page 3: Relationships ---------------------------------------------------
TEXTBOX_TEXT = ("log GDP vs mortality: r = -0.77 | health spend per capita: r = -0.76 | "
                "health spend % GDP: r = -0.22. Absolute per-capita health investment "
                "predicts child survival; budget share alone does not.")
textbox = {"$schema": SCHEMAS["visualContainer"], "name": vid(),
           "position": {"x": 12, "y": 12, "z": 0, "width": 1256, "height": 64},
           "visual": {"visualType": "textbox",
                      "objects": {"general": [{"properties": {"paragraphs": [
                          {"textRuns": [{"value": TEXTBOX_TEXT,
                                         "textStyle": {"fontSize": "12pt"}}]}]}}]},
                      "drillFilterOtherVisuals": True}}
scatter = visual(
    "scatterChart", (12, 88, 1256, 620),
    {"Category": bucket(proj(col(LATEST, "country"), LATEST, "country")),
     "Series": bucket(proj(col(LATEST, "region"), LATEST, "region")),
     "X": bucket(proj(meas(LATEST, "GDP per Capita 2023"), LATEST, "GDP per Capita 2023")),
     "Y": bucket(proj(meas(LATEST, "Avg Mortality 2023"), LATEST, "Avg Mortality 2023")),
     "Size": bucket(proj(meas(LATEST, "Health Spend per Capita 2023"),
                         LATEST, "Health Spend per Capita 2023"))},
    objects={"categoryAxis": [{"properties": {
        "axisScale": {"expr": {"Literal": {"Value": "'log'"}}}}}]},
    filter_config=year_filter(LATEST, "latest_year", 2023), z=1)
p3 = [textbox, scatter]

# ---- pages + report shell -----------------------------------------------------
PAGES = [("KPI Overview", p1), ("Geography & Distribution", p2), ("Relationships", p3)]
page_names = []
for display, visuals in PAGES:
    pname = vid()
    page_names.append(pname)
    pdir = os.path.join(RPT, "definition", "pages", pname)
    write_json(os.path.join(pdir, "page.json"),
               {"$schema": SCHEMAS["page"], "name": pname, "displayName": display,
                "displayOption": "FitToPage", "height": 720, "width": 1280})
    for v in visuals:
        write_json(os.path.join(pdir, "visuals", v["name"], "visual.json"), v)

write_json(os.path.join(RPT, "definition", "pages", "pages.json"),
           {"$schema": SCHEMAS["pagesMetadata"], "pageOrder": page_names,
            "activePageName": page_names[0]})
write_json(os.path.join(RPT, "definition", "report.json"),
           {"$schema": SCHEMAS["report"],
            "themeCollection": {"baseTheme": {
                "name": "CY24SU10",
                "reportVersionAtImport": {"visual": "2.4.0", "page": "2.1.0",
                                          "report": "3.0.0"},
                "type": "SharedResources"}}})
write_json(os.path.join(RPT, "definition", "version.json"),
           {"$schema": SCHEMAS["versionMetadata"], "version": "2.0.0"})
write_json(os.path.join(RPT, "definition.pbir"),
           {"$schema": SCHEMAS["pbir"], "version": "4.0",
            "datasetReference": {"byPath": {"path": "../GlobalHealthEquity.SemanticModel"}}})
write_json(os.path.join(RPT, ".platform"),
           {"$schema": SCHEMAS["platform"],
            "metadata": {"type": "Report", "displayName": "GlobalHealthEquity"},
            "config": {"version": "2.0", "logicalId": gid()}})

write_json(os.path.join(PRJ, "GlobalHealthEquity.pbip"),
           {"$schema": SCHEMAS["pbip"], "version": "1.0",
            "artifacts": [{"report": {"path": "GlobalHealthEquity.Report"}}],
            "settings": {"enableAutoRecovery": True}})

print("\nDone. Project at", PRJ)

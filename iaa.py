import os
import json

from pyld import jsonld

IAA_CONF_FILE = os.getenv("IAA_CONF_FILE", "IAA.conf")
OWNER_DID = os.getenv("OWNER_DID", "did:self:1234oiuerhg98043n9hve")
PROXY_PASS = os.getenv("PROXY_PASS", "http://127.0.0.1:8000")

LD_ACCESS_REQUIREMENTS = "https://twinschema.org/accessRequirements"
LD_LOCATION = "http://www.w3.org/2003/01/geo/wgs84_pos#location"
LD_NEIGHBOURHOOD = "https://saref.etsi.org/saref4city/Neighbourhood"

# Initialize a conf file
iaa_conf = {
    "resources": {
        "/twins": {
            "authorization": {
                "type": "jwt-vc-dpop",
                "trusted_issuers": {
                    OWNER_DID: {"issuer_key": OWNER_DID, "issuer_key_type": "did"}
                },
                "filters": [
                    [
                        "$.vc.credentialSubject.capabilities.'https://iot-ngin.twinbase.org/twins'[*]",
                        "READ",
                    ]
                ],
            },
            "proxy": {"proxy_pass": PROXY_PASS},
        },
        "/docs": {"proxy": {"proxy_pass": PROXY_PASS}},
        "/openapi.json": {"proxy": {"proxy_pass": PROXY_PASS}},
        "/favicon.ico": {"proxy": {"proxy_pass": PROXY_PASS}},
    }
}


def get_conf_twin_template() -> dict:
    return {
        "authorization": {
            "type": "jwt-vc-dpop",
            "trusted_issuers": {
                OWNER_DID: {"issuer_key": OWNER_DID, "issuer_key_type": "did"}
            },
            "filters": [
                [
                    "$.vc.credentialSubject.capabilities.'https://iot-ngin.twinbase.org/twins'[*]",
                    "READ",
                ]
            ],
        },
        "proxy": {"proxy_pass": PROXY_PASS},
    }


def configure(twin: dict, filters: list[str]) -> None:
    """Define twin conf"""

    try:
        with open(IAA_CONF_FILE, "r") as jsonfiler:
            conf = json.load(jsonfiler)
    except FileNotFoundError:
        print("IAA.conf not found, creating new from template.")
        conf = iaa_conf

    conf_twin = get_conf_twin_template()
    print("Conf template: " + str(conf_twin))

    for filter_content in filters:
        print("Creating filter: " + filter_content)
        filter = [f"$.vc.credentialSubject.capabilities.'{filter_content}'[*]", "READ"]
        conf_twin["authorization"]["filters"].append(filter)

    local_id = twin["dt-id"].split("/")[3]
    conf["resources"]["/twins/" + local_id] = conf_twin

    with open(IAA_CONF_FILE, "w", encoding="utf-8") as jsonfilew:
        json.dump(conf, jsonfilew, indent=4, ensure_ascii=False)

    print(conf_twin)


def get_location_filters_for(document: dict) -> list[str]:
    filters: list[str] = []
    expanded_doc = jsonld.expand(document)

    if not len(expanded_doc) > 0:
        print("Found no linked data.")
        return filters

    if LD_LOCATION not in expanded_doc[0]:
        print(f"Found linked data, but not {LD_LOCATION}")
        return filters

    loc = expanded_doc[0][LD_LOCATION]

    if type(loc) is dict:
        print("One location definitions found")
        print("Value: " + loc["@value"])
        filters.append(f"{LD_NEIGHBOURHOOD} = {loc['@value']}")

    elif type(loc) is list:
        print("Several location definitions found")
        for location in loc:
            print(f"Type: {location['@type']} Value: {location['@value']}")
            # This @type & @value style was used at least in:
            # https://csiro-enviro-informatics.github.io/info-engineering/linked-data-api.html
            if location["@type"] == LD_NEIGHBOURHOOD:
                print("Found neighbourhood!")
                filters.append(f"{LD_NEIGHBOURHOOD} = {location['@value']}")
                print("Appended neighbourhood filter.")

    return filters

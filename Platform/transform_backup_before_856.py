from lxml import etree

def xml_to_canonical(raw_xml: str) -> dict:
    root = etree.fromstring(raw_xml.encode("utf-8"))
    po_number = root.xpath("string(//poNumber)")
    return {
        "poNumber": po_number,
        "status": "PARSED"
    }

def canonical_to_netsuite_payload(canonical: dict) -> dict:
    return {
        "otherRefNum": canonical.get("poNumber"),
        "memo": "Created via thesis platform prototype"
    }

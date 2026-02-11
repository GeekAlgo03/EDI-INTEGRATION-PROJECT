from lxml import etree


# -------- 850 --------
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


# -------- 856 --------
def xml_856_to_canonical(raw_xml: str) -> dict:
    root = etree.fromstring(raw_xml.encode("utf-8"))

    shipment_number = root.xpath(
        "string(//*[local-name()='shipmentIdentificationNumber'])"
    )
    po_number = root.xpath(
        "string(//*[local-name()='poNumber'])"
    )

    items = []
    for item in root.xpath("//*[local-name()='item']"):
        items.append({
            "sku": item.xpath("string(.//*[local-name()='itemIdentifier'])"),
            "quantity": item.xpath("string(.//*[local-name()='quantityShipped'])")
        })

    return {
        "shipmentNumber": shipment_number,
        "poNumber": po_number,
        "items": items,
        "status": "PARSED_856"
    }


def canonical_856_to_netsuite_payload(canonical: dict) -> dict:
    return {
        "createdFrom": canonical.get("poNumber"),
        "shipStatus": "SHIPPED",
        "shipmentNumber": canonical.get("shipmentNumber"),
        "items": canonical.get("items", []),
        "memo": "856 ASN created via thesis platform prototype"
    }

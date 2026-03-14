from lxml import etree


# -------- 850 --------
def xml_to_canonical(raw_xml: str) -> dict:
    root = etree.fromstring(raw_xml.encode("utf-8"))

    po_number = root.xpath("string(//poNumber)")
    qty_ordered = root.xpath("string(//lineItem/qtyOrdered)")
    order_date = root.xpath("string(//orderDate)")

    return {
        "poNumber": po_number,
        "qtyOrdered": qty_ordered,
        "orderDate": order_date,
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
    ship_date = root.xpath(
        "string(//*[local-name()='shipDate'])"
    )

    items = []
    for item in root.xpath("//*[local-name()='item']"):
        item_po = item.xpath("string(.//*[local-name()='poNumber'])")

        # If item-level poNumber exists, only take items for the same PO
        if item_po and item_po != po_number:
            continue

        items.append({
            "sku": item.xpath("string(.//*[local-name()='itemIdentifier'])"),
            "quantity": item.xpath("string(.//*[local-name()='quantityShipped'])")
        })

    return {
        "shipmentNumber": shipment_number,
        "poNumber": po_number,
        "shipDate": ship_date,
        "items": items,
        "status": "PARSED_856"
    }


def canonical_856_to_netsuite_payload(canonical: dict) -> dict:
    return {
        "createdFrom": canonical.get("poNumber"),
        "shipStatus": "SHIPPED",
        "shipmentNumber": canonical.get("shipmentNumber"),
        "shipDate": canonical.get("shipDate"),
        "items": canonical.get("items", []),
        "memo": "856 ASN created via thesis platform prototype"
    }

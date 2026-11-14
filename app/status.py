"""UI-neutral mapping from an engine row's flag to a preview status."""


def status_of(row):
    flag = row.get("flag") or ""
    if flag == "facturado":
        return "FACTURADO"
    if flag == "revisar":
        return "REVISAR"
    if row.get("driver") and row.get("milage") is not None:
        if flag == "sugerido":
            return "SUGERIDO"
        if flag == "balanceado":
            return "BALANCEADO"
        return "NOTA" if flag == "nota" else "OK"
    if flag == "nofacturar":
        return "NO FACTURAR"
    if not row.get("driver"):
        return "ELEGIR" if row.get("milage") is not None else "SIN DATO"
    return "REVISAR"

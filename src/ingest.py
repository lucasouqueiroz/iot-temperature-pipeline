def read_csv_flexible(path: Path) -> pd.DataFrame:
    """Lê o CSV original do Kaggle separado por vírgulas."""
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}. "
            "Coloque o CSV em data/IOT-temp.csv."
        )

    return pd.read_csv(path, sep=",", encoding="utf-8-sig")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as colunas originais para o modelo do projeto."""
    required = {"id", "room_id/id", "noted_date", "temp", "out/in"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Colunas ausentes no CSV: {sorted(missing)}")

    result = pd.DataFrame({
        "room": df["room_id/id"].astype("string").str.strip(),
        "reading_at": pd.to_datetime(
            df["noted_date"],
            format="%d-%m-%Y %H:%M",
            errors="coerce",
        ),
        "temperature": pd.to_numeric(df["temp"], errors="coerce"),
        "direction": df["out/in"].astype("string").str.strip(),
    })

    invalid = (
        result["reading_at"].isna()
        | result["temperature"].isna()
        | result["room"].isna()
        | result["room"].eq("")
        | ~result["direction"].isin(["In", "Out"])
    )

    if invalid.any():
        raise ValueError(
            f"Foram encontradas {int(invalid.sum())} linhas inválidas. "
            "A carga foi interrompida para evitar descarte silencioso."
        )

    # Agrupamento analítico, não identificador de um sensor físico.
    result["device_id"] = result["room"] + " / " + result["direction"]

    return result[
        ["device_id", "room", "reading_at", "temperature", "direction"]
    ]
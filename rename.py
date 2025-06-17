from pathlib import Path

DST_ROOT = Path("data_v2")

def corregir_nombres():
    """
    Busca en data_v2/{Continent}/{ISO}/{ISO}_boundarie.geojson
    y lo renombra a boundarie.geojson.
    """
    for continent_dir in DST_ROOT.iterdir():
        if not continent_dir.is_dir():
            continue

        for iso_dir in continent_dir.iterdir():
            if not iso_dir.is_dir():
                continue

            # Ruta al archivo con prefijo ISO_
            src_file = iso_dir / f"{iso_dir.name}_boundarie.geojson"
            dst_file = iso_dir / "boundarie.geojson"

            if src_file.exists():
                # Si ya existe un boundarie.geojson previo, lo avisamos y lo omitimos
                if dst_file.exists():
                    print(f"⚠️ Ya existe {dst_file}, omitiendo.")
                else:
                    src_file.rename(dst_file)
                    print(f"✅ Renombrado: {src_file.name} → {dst_file.name}")
            else:
                print(f"⚠️ No encontrado: {src_file}")

if __name__ == "__main__":
    corregir_nombres()
    print("¡Todos los archivos actualizados! 🎉")

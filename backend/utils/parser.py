def parse_task(text):
    hasil = {}

    for line in text.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        hasil[key.strip().lower()] = value.strip()

    return hasil
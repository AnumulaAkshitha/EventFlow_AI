import os
import qrcode

def generate_qr(registration_id):

    folder = "static/qr"

    os.makedirs(folder, exist_ok=True)

    filename = f"{registration_id}.png"

    filepath = os.path.join(folder, filename)

    img = qrcode.make(registration_id)

    img.save(filepath)

    return filepath
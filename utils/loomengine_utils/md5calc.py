import hashlib

def calculate_md5sum(file_path):
    with open(file_path, 'rb') as f:
        m = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            m.update(data)
    return m.hexdigest()

def calculate_md5sum_from_string(string):
    m = hashlib.md5(string)

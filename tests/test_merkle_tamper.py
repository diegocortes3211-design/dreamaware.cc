from services.audit.merkle import merkle_root

def test_merkle_detects_tamper():
    a = [b'{"k":1}', b'{"k":2}', b'{"k":3}']
    b = [b'{"k":1}', b'{"k":2}', b'{"k":3!}'] # 1 byte changed
    assert merkle_root(a) != merkle_root(b)
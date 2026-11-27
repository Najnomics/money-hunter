"""Local HMAC distinguishing test. Never hits omni.variational.io."""
import hashlib
import hmac
import sys

KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SECRET = "11" * 32


def sign(key, secret, ts, method, path, body=b""):
    msg = f"{key}|{ts}|{method}|{path}".encode()
    signer = hmac.new(bytes.fromhex(secret), msg, hashlib.sha256)
    if body:
        signer.update(b"|")
        signer.update(body)
    return signer.hexdigest()


def main():
    a = sign(KEY, SECRET, 1, "GET", "/v1/x")
    b = sign(KEY, SECRET, 2, "GET", "/v1/x")
    assert a != b, "timestamp not bound"
    c = sign(KEY, SECRET, 1, "POST", "/v1/x", b'{"a":1}')
    d = sign(KEY, SECRET, 1, "POST", "/v1/x", b'{"a":2}')
    assert c != d, "body not bound"
    forged = sign(KEY, "00" * 32, 1, "GET", "/v1/x")
    assert forged != a, "wrong secret still matches"
    print("hmac-local: PASS timestamp+body bound; wrong secret differs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

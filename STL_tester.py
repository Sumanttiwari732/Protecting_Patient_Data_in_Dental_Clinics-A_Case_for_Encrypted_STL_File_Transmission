"""
STL File AES-256-GCM Encryption Test Suite
===========================================

What this script does:
    1. Collects 45 STL files (downloads real ones from GitHub; generates
       synthetic ones to fill the rest — no API key needed).
    2. Encrypts each file with AES-256-GCM using a random 96-bit nonce.
    3. Decrypts each encrypted file and checks the result matches the original.
    4. Runs a tamper test: flips a byte in the ciphertext and confirms
       AES-GCM raises an error (proving authentication works).
    5. Saves results to results.csv and a human-readable report.txt.

Requirements:
    pip install cryptography

Usage:
    python stl_aes256gcm_tester.py

Output folders created automatically:
    stl_files/        — downloaded or generated STL files
    encrypted_files/  — AES-256-GCM encrypted versions (.enc)
    decrypted_files/  — decrypted files (should be identical to originals)
    results.csv       — per-file benchmark and test results
    report.txt        — summary report
"""

import csv
import hashlib
import secrets
import struct
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.exit("Missing library. Run:  pip install cryptography")


# ── Settings (edit these if needed) ──────────────────────────────────────────

TARGET_FILE_COUNT = 45       # Total STL files to test
NONCE_SIZE        = 12       # 96-bit nonce — GCM standard recommendation
KEY_SIZE          = 32       # 256-bit AES key
# AAD = Additional Authenticated Data: binds encrypted files to this context.
# Any change to AAD makes decryption fail, even with the correct key.
AAD = b"STL-AES256GCM-TEST-v1"

# Output folders
STL_DIR = Path("stl_files")
ENC_DIR = Path("encrypted_files")
DEC_DIR = Path("decrypted_files")


# ── Real STL files from public GitHub repositories (open-license) ─────────────
# These are actual 3D model files used in well-known open-source projects.
REAL_STL_URLS = [
    # Three.js example models (MIT license)
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/ascii/pr2_head_pan.stl",
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/ascii/pr2_head_tilt.stl",
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/binary/pr2_head_pan.stl",
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/binary/pr2_head_tilt.stl",
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/ascii/slotted_disk.stl",
    "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/stl/ascii/galeon.stl",
    # Prusa Research printer parts (GNU AGPL license)
    "https://raw.githubusercontent.com/prusa3d/Original-Prusa-i3/master/Printed-Parts/stl/y-belt-idler.stl",
    "https://raw.githubusercontent.com/prusa3d/Original-Prusa-i3/master/Printed-Parts/stl/y-belt-holder.stl",
    "https://raw.githubusercontent.com/prusa3d/Original-Prusa-i3/master/Printed-Parts/stl/pinda-mount.stl",
    "https://raw.githubusercontent.com/prusa3d/Original-Prusa-i3/master/Printed-Parts/stl/lcd-support-left.stl",
    "https://raw.githubusercontent.com/prusa3d/Original-Prusa-i3/master/Printed-Parts/stl/lcd-support-right.stl",
]


# ── Step 1: Collect STL files ─────────────────────────────────────────────────

def download_stl(url: str, destination: Path) -> bool:
    """Download a single STL file. Returns True if successful."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        # A valid binary STL is at least 84 bytes (80-byte header + 4-byte count).
        # ASCII STL starts with 'solid'. Either way, skip tiny/empty responses.
        if len(data) < 84:
            return False
        destination.write_bytes(data)
        return True
    except Exception:
        return False


def make_synthetic_stl(destination: Path, num_triangles: int) -> None:
    """
    Generate a structurally valid binary STL file with random triangle data.

    Binary STL format:
        - 80 bytes: header (any text)
        - 4 bytes:  number of triangles (uint32, little-endian)
        - Per triangle (50 bytes each):
            - 12 bytes: normal vector (3 x float32)
            - 36 bytes: 3 vertices (3 x 3 x float32)
            - 2 bytes:  attribute byte count (usually 0)
    """
    with open(destination, "wb") as f:
        header = b"Synthetic STL - AES-256-GCM encryption test file" + b"\x00" * 31
        f.write(header[:80])
        f.write(struct.pack("<I", num_triangles))
        for _ in range(num_triangles):
            # 50 random bytes = valid triangle geometry (random coordinates)
            f.write(bytes(secrets.randbelow(256) for _ in range(50)))


def collect_stl_files() -> List[Path]:
    """
    Build a list of STL files to test.
    - First tries to download real STL files from GitHub.
    - Generates synthetic STL files to reach the TARGET_FILE_COUNT.
    """
    STL_DIR.mkdir(exist_ok=True)
    files: List[Path] = []

    print(f"\n[STEP 1] Collecting {TARGET_FILE_COUNT} STL files")
    print("-" * 55)

    # Try downloading real STL files
    for url in REAL_STL_URLS:
        if len(files) >= TARGET_FILE_COUNT:
            break
        filename = url.split("/")[-1]
        dest = STL_DIR / filename
        # Skip re-downloading if the file already exists
        if dest.exists() and dest.stat().st_size >= 84:
            files.append(dest)
            print(f"  [cached] {filename}")
            continue
        success = download_stl(url, dest)
        if success:
            files.append(dest)
            print(f"  [downloaded] {filename}  ({dest.stat().st_size:,} bytes)")
        else:
            print(f"  [failed]     {filename}")

    # Fill remaining slots with synthetic STL files of varying sizes
    # Triangle counts chosen to produce a range of file sizes for a realistic benchmark
    triangle_counts = [100, 250, 500, 1000, 2000, 5000, 10000, 20000]
    i = 0
    while len(files) < TARGET_FILE_COUNT:
        num_triangles = triangle_counts[i % len(triangle_counts)] + (i * 41 % 500)
        filename = f"synthetic_{i+1:03d}_{num_triangles}tri.stl"
        dest = STL_DIR / filename
        if not dest.exists():
            make_synthetic_stl(dest, num_triangles)
        files.append(dest)
        print(f"  [generated] {filename}  ({dest.stat().st_size:,} bytes)")
        i += 1

    print(f"\n  Ready: {len(files)} STL files total")
    return files


# ── Step 2: AES-256-GCM encrypt / decrypt ────────────────────────────────────

def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt bytes using AES-256-GCM.

    Returns: nonce (12 bytes) + ciphertext + GCM authentication tag (16 bytes).

    The nonce is randomly generated for each call — this is required for GCM
    security. Reusing a nonce with the same key breaks confidentiality.
    """
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext_and_tag = AESGCM(key).encrypt(nonce, plaintext, AAD)
    # Prepend nonce so the decryptor knows what was used
    return nonce + ciphertext_and_tag


def decrypt(payload: bytes, key: bytes) -> bytes:
    """
    Decrypt an AES-256-GCM payload produced by encrypt().

    Raises cryptography.exceptions.InvalidTag if the ciphertext or AAD
    has been tampered with — this is the authentication guarantee of GCM.
    """
    nonce      = payload[:NONCE_SIZE]
    ciphertext = payload[NONCE_SIZE:]
    return AESGCM(key).decrypt(nonce, ciphertext, AAD)


# ── Result storage ─────────────────────────────────────────────────────────────

@dataclass
class Result:
    file_name:          str
    file_size_bytes:    int
    encrypt_time_ms:    float
    decrypt_time_ms:    float
    encrypt_mbps:       float   # throughput: how fast encryption ran
    decrypt_mbps:       float
    sha256_match:       bool    # True if decrypted file == original file
    gcm_tag_verified:   bool    # True if GCM authentication passed
    tamper_detected:    bool    # True if bit-flip in ciphertext was caught
    passed:             bool    # True if all three checks above passed
    error:              Optional[str] = None


# ── Step 3: Run tests ─────────────────────────────────────────────────────────

def run_tests(stl_files: List[Path]) -> List[Result]:
    """
    For each STL file:
      (a) Encrypt with AES-256-GCM and measure speed
      (b) Decrypt and verify the file is byte-identical to the original
      (c) Tamper test: corrupt one ciphertext byte and confirm GCM rejects it
    """
    ENC_DIR.mkdir(exist_ok=True)
    DEC_DIR.mkdir(exist_ok=True)

    # One shared key for this test session.
    # In production, use a unique key per file or per user.
    key = secrets.token_bytes(KEY_SIZE)

    print(f"\n[STEP 2] Running AES-256-GCM tests")
    print(f"  Key: {KEY_SIZE*8}-bit  |  Nonce: {NONCE_SIZE*8}-bit random  |  Tag: 128-bit")
    print("-" * 65)
    print(f"  {'#':>3}  {'File':<32} {'Bytes':>8}  {'Enc ms':>7}  {'Dec ms':>7}  {'MB/s':>7}  {'OK':>4}")
    print(f"  {'─'*3}  {'─'*32} {'─'*8}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*4}")

    results = []

    for idx, path in enumerate(stl_files, 1):
        try:
            original_bytes = path.read_bytes()
            file_size      = len(original_bytes)
            sha_original   = hashlib.sha256(original_bytes).hexdigest()

            # (a) Encrypt and save
            t0      = time.perf_counter()
            payload = encrypt(original_bytes, key)
            enc_ms  = (time.perf_counter() - t0) * 1000
            (ENC_DIR / (path.name + ".enc")).write_bytes(payload)

            # (b) Decrypt and compare to original
            t1        = time.perf_counter()
            recovered = decrypt(payload, key)
            dec_ms    = (time.perf_counter() - t1) * 1000
            (DEC_DIR / path.name).write_bytes(recovered)

            sha_recovered = hashlib.sha256(recovered).hexdigest()
            sha_match     = sha_original == sha_recovered
            gcm_ok        = True   # decrypt() above would have raised if GCM tag failed

            # (c) Tamper test: flip one byte in the ciphertext body
            #     (byte at NONCE_SIZE+4 is inside the ciphertext, not the nonce)
            tampered_payload          = bytearray(payload)
            tampered_payload[NONCE_SIZE + 4] ^= 0xFF
            tamper_caught = False
            try:
                decrypt(bytes(tampered_payload), key)
            except Exception:
                tamper_caught = True  # expected — GCM should reject any modification

            # Speed in MB/s
            mb       = file_size / (1024 * 1024)
            enc_mbps = mb / (enc_ms / 1000) if enc_ms > 0 else 0
            dec_mbps = mb / (dec_ms / 1000) if dec_ms > 0 else 0

            passed = sha_match and gcm_ok and tamper_caught
            mark   = "✓" if passed else "✗"
            print(f"  {idx:>3}  {path.name:<32} {file_size:>8,}  {enc_ms:>7.2f}  {dec_ms:>7.2f}  {enc_mbps:>7.1f}  {mark:>4}")

            results.append(Result(
                file_name       = path.name,
                file_size_bytes = file_size,
                encrypt_time_ms = round(enc_ms, 3),
                decrypt_time_ms = round(dec_ms, 3),
                encrypt_mbps    = round(enc_mbps, 2),
                decrypt_mbps    = round(dec_mbps, 2),
                sha256_match    = sha_match,
                gcm_tag_verified= gcm_ok,
                tamper_detected = tamper_caught,
                passed          = passed,
            ))

        except Exception as exc:
            print(f"  {idx:>3}  {path.name:<32} {'ERROR':>8}  {'─':>7}  {'─':>7}  {'─':>7}  ✗")
            results.append(Result(
                file_name=path.name, file_size_bytes=0,
                encrypt_time_ms=0, decrypt_time_ms=0,
                encrypt_mbps=0, decrypt_mbps=0,
                sha256_match=False, gcm_tag_verified=False,
                tamper_detected=False, passed=False,
                error=str(exc),
            ))

    return results


# ── Step 4: Save results ──────────────────────────────────────────────────────

def save_csv(results: List[Result], path: Path = Path("results.csv")) -> None:
    """Write per-file results to a CSV file."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)
    print(f"\n  CSV saved  → {path}")


def save_report(results: List[Result], path: Path = Path("report.txt")) -> None:
    """Write a human-readable summary report."""
    passed   = [r for r in results if r.passed]
    failed   = [r for r in results if not r.passed]
    total_mb = sum(r.file_size_bytes for r in results) / (1024 * 1024)

    enc_speeds = [r.encrypt_mbps for r in passed if r.encrypt_mbps > 0]
    dec_speeds = [r.decrypt_mbps for r in passed if r.decrypt_mbps > 0]

    def avg(lst): return sum(lst) / len(lst) if lst else 0

    lines = [
        "=" * 60,
        "  AES-256-GCM STL FILE ENCRYPTION — TEST REPORT",
        "=" * 60,
        "",
        "  Algorithm settings",
        f"    Algorithm : AES-256-GCM",
        f"    Key size  : {KEY_SIZE * 8} bits",
        f"    Nonce     : {NONCE_SIZE * 8} bits, random per file",
        f"    Tag size  : 128 bits (GCM default)",
        f"    AAD       : {AAD.decode()}",
        "",
        "  Test summary",
        f"    Files tested : {len(results)}",
        f"    Passed       : {len(passed)}",
        f"    Failed       : {len(failed)}",
        f"    Total data   : {total_mb:.2f} MB",
        "",
        "  Encryption speed (passed files only)",
        f"    Average : {avg(enc_speeds):.1f} MB/s",
        f"    Min     : {min(enc_speeds):.1f} MB/s" if enc_speeds else "    Min : N/A",
        f"    Max     : {max(enc_speeds):.1f} MB/s" if enc_speeds else "    Max : N/A",
        "",
        "  Decryption speed (passed files only)",
        f"    Average : {avg(dec_speeds):.1f} MB/s",
        f"    Min     : {min(dec_speeds):.1f} MB/s" if dec_speeds else "    Min : N/A",
        f"    Max     : {max(dec_speeds):.1f} MB/s" if dec_speeds else "    Max : N/A",
        "",
        "  Security checks",
        f"    SHA-256 integrity : {sum(r.sha256_match    for r in results)}/{len(results)} passed",
        f"    GCM tag verified  : {sum(r.gcm_tag_verified for r in results)}/{len(results)} passed",
        f"    Tamper detected   : {sum(r.tamper_detected  for r in results)}/{len(results)} passed",
    ]

    if failed:
        lines += ["", "  Failed files"]
        for r in failed:
            lines.append(f"    ✗ {r.file_name}  ({r.error or 'check failed'})")

    lines += [
        "",
        "  Per-file results",
        f"  {'File':<35} {'Bytes':>8}  {'Enc MB/s':>9}  {'Dec MB/s':>9}  {'Pass':>5}",
        f"  {'─'*35} {'─'*8}  {'─'*9}  {'─'*9}  {'─'*5}",
    ]
    for r in results:
        lines.append(
            f"  {r.file_name:<35} {r.file_size_bytes:>8,}"
            f"  {r.encrypt_mbps:>9.1f}  {r.decrypt_mbps:>9.1f}"
            f"  {'YES' if r.passed else 'NO':>5}"
        )

    lines += ["", "=" * 60]
    report_text = "\n".join(lines)
    path.write_text(report_text)
    print(f"  Report saved → {path}")
    print("\n" + report_text)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  STL File AES-256-GCM Encryption Test Suite")
    print("=" * 60)

    stl_files = collect_stl_files()
    results   = run_tests(stl_files)
    save_csv(results)
    save_report(results)

    print(f"\n  Encrypted files → {ENC_DIR}/")
    print(f"  Decrypted files → {DEC_DIR}/")

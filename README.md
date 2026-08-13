# STL File AES-256-GCM Encryption — Dental Clinic Data Protection

A lightweight Python tool that encrypts 3D dental scan files (STL format) before transmission to external laboratories, protecting biometric patient data under GDPR and HIPAA.

---

## Why this exists

Dental clinics send STL files — detailed 3D maps of a patient's teeth — to outside labs every day. Most send them by plain email. Under GDPR Article 4(14), STL files qualify as **biometric data**. Under GDPR Article 4(15), they also qualify as **health data**. Both categories carry the highest level of legal protection available.

Plain email is not encrypted. A file intercepted in transit exposes permanent, irreplaceable patient data. Unlike a stolen password, biometric data cannot be changed.

New HIPAA Security Rule revisions proposed for 2026 will make encryption mandatory for all protected health information in transit, with no exceptions.

---

## What the tool does

1. Encrypts an STL file using AES-256-GCM — the same standard used by the U.S. federal government for classified information.
2. Produces an encrypted file that cannot be opened without the matching key.
3. Decrypts the file at the lab end, restoring it byte-for-byte to its original state.
4. Generates an authentication tag that confirms the file was not altered during transit.

The encrypted file travels by email as usual. The key is sent separately — by text message or secure messenger. An attacker who intercepts the email gets a file they cannot use.

---

## How it works

```
Clinic                              Lab
  │                                  │
  ├─ Load STL file                   │
  ├─ Generate random 96-bit nonce    │
  ├─ Encrypt with AES-256-GCM ──────►│
  ├─ Send key via separate channel ─►│
  │                                  ├─ Receive encrypted file
  │                                  ├─ Receive key (separate)
  │                                  ├─ Decrypt with AES-256-GCM
  │                                  ├─ Verify GCM authentication tag
  │                                  └─ Open STL file in software
```

---

## Encryption details

| Parameter | Value | Why |
|---|---|---|
| Algorithm | AES-256-GCM | FIPS 140-2 compliant; provides both encryption and authentication |
| Key size | 256 bits | U.S. federal standard for top-secret classification |
| Nonce | 96 bits, random per file | Required for GCM security — never reuse a nonce with the same key |
| Authentication tag | 128 bits | Detects any modification to the encrypted file |
| AAD | `STL-AES256GCM-TEST-v1` | Binds the ciphertext to this specific application context |

---

## Requirements

```
pip install cryptography
```

No other dependencies. No hardware changes. No vendor contracts.

---

## Usage

```bash
python stl_aes256gcm_tester.py
```

The script:
- Downloads real STL files from public GitHub repositories (Three.js models, Prusa printer parts)
- Generates synthetic STL files to reach 45 test files if downloads fail
- Encrypts each file, decrypts it, and verifies the result matches the original
- Runs a tamper test: flips one byte in the ciphertext and confirms GCM raises an error
- Saves results to `results.csv` and `report.txt`

---

## Output folders

```
stl_files/        — original STL files (downloaded or generated)
encrypted_files/  — AES-256-GCM encrypted versions (.enc)
decrypted_files/  — decrypted files (byte-identical to originals)
results.csv       — per-file benchmark and pass/fail results
report.txt        — summary report with performance statistics
```

---

## Test results (45 files)

| Check | Result |
|---|---|
| SHA-256 integrity match | 45 / 45 |
| GCM authentication tag verified | 45 / 45 |
| Tamper detection (bit-flip test) | 45 / 45 |
| Average encryption speed | ~1,015 MB/s |
| Average decryption speed | ~1,417 MB/s |
| Average time per file | < 1 ms |

All files decrypt to byte-identical copies of the originals. No standard software can open an encrypted file without the key.

---

## Validation plan

Three tests confirm the solution works before clinical adoption:

**1. File integrity** — SHA-256 hash of the decrypted file must match the original. Any corruption during encryption or decryption changes the hash completely. Pass rate must be 100%.

**2. Processing time** — Average time across all file sizes must stay under 5 seconds. Dental STL files range from 1 to 10 MB. AES-256-GCM processes files of that size in under 1 millisecond on standard consumer hardware.

**3. Unreadability** — Encrypted files must fail to open in a text editor, an STL viewer, and a generic file explorer. This confirms the encryption is real, not just a file rename.

---

## Compliance coverage

| Requirement | Standard | Status with this tool |
|---|---|---|
| Transmission security | HIPAA 45 C.F.R. § 164.312(e) | Covered |
| Encryption mandatory (2026) | Proposed HIPAA Security Rule | Pre-compliant |
| Integrity and confidentiality | GDPR Article 5(1)(f) | Covered |
| Special category data protection | GDPR Article 9 | Covered |
| Breach notification mitigating factor | GDPR Article 33 | Encryption is documented mitigator |

---

## Broader use

The same script works for any small healthcare provider transmitting sensitive files by email — radiology images, pathology reports, optometry scans. The file format does not matter. Only the key size and algorithm matter, and both are already set correctly.

---

## References

- European Parliament & Council of the EU. (2016). *General Data Protection Regulation (EU) 2016/679*.
- U.S. Department of Health and Human Services. (2003). *HIPAA Security Rule. 45 C.F.R. pts. 160, 162, and 164.*
- U.S. Department of Health and Human Services. (2025). *HIPAA Security Rule to strengthen the cybersecurity of electronic protected health information.* Office for Civil Rights.
- IBM Security. (2024). *Cost of a data breach report 2024.*
- Verizon. (2024). *2024 data breach investigations report.*

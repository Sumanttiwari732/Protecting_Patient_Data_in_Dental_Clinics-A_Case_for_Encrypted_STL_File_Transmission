Protecting Patient Data in Dental Clinics:
A Case for Encrypted STL File Transmission


Introduction

Dental clinics send digital tooth scans to outside laboratories every day. These scans, called STL files, contain a detailed three-dimensional image of a patient's teeth. Under the General Data Protection Regulation (GDPR), this kind of data is classified as biometric data. It is unique to each person, just like a fingerprint or a facial scan. Most clinics send these files by standard email, and most email is not encrypted. If someone intercepts that message, they can access permanent, irreplaceable patient data.

This paper explains why that practice is dangerous, proposes a specific technical fix, and describes how to confirm the fix works. The goal is to persuade clinic administrators to act before a breach occurs and before updated regulations force their hand.

1. Problem Identification and Definition

Statement of the Problem

Dental clinics routinely transmit STL files to external dental laboratories. An STL file contains a precise three-dimensional map of a patient's teeth, palate, and oral anatomy. Under GDPR Article 4(14), this qualifies as biometric data because it results from technical processing of physical characteristics and can uniquely identify a person. Under GDPR Article 4(15), the same file also qualifies as health data because it reveals the patient's dental conditions, missing teeth, and bone structure. This means every STL file carries the highest level of protection available under GDPR.

Despite this, most clinics transfer these files using standard email or basic consumer file-sharing services. During transmission, files pass through multiple servers. Any one of those servers can be a point of interception. The data is exposed at every step, and neither the clinic nor the patient may ever know.

Justification

This problem affects a large number of patients across the entire dental sector. A single clinic may send 20 to 50 STL files per week, which adds up to more than 1,000 unprotected transmissions per year from one location alone. Healthcare data is consistently one of the most targeted categories in cyberattacks. The 2024 Verizon Data Breach Investigations Report identified healthcare as one of the top sectors for confirmed breaches. The IBM Security Cost of a Data Breach Report (2024) found that healthcare breaches now carry the highest average cost of any industry. These figures make the financial and ethical cost of inaction clear.

The legal pressure is also growing. The U.S. Department of Health and Human Services proposed significant revisions to the HIPAA Security Rule. These revisions would eliminate the distinction between addressable and required safeguards, making encryption mandatory for all electronic protected health information in transit. The proposed rule is on the OCR regulatory agenda for May 2026. 

Supporting Arguments

The risk of sending unencrypted STL files is not theoretical. Biometric data has real value to attackers. It can be used for identity fraud, insurance fraud, and targeted deception. Unlike a stolen password, it cannot be changed once it is taken. The harm is permanent. Standard email was not designed to protect sensitive health data. Files sent this way travel through multiple intermediary servers, any of which can be compromised.

GDPR Article 5(1)(f) requires that personal data be processed using appropriate technical measures to ensure security, including protection against unauthorized access and accidental loss. For special category data like STL files, this means encryption is not optional. It is a legal requirement. Article 9(1) prohibits the processing of biometric and health data except under narrow exceptions, and any breach of that data triggers a 72-hour notification obligation to the supervisory authority. If the breach creates high risk for individuals, direct notification to affected patients is also required (European Parliament, 2016).

The 2003 HIPAA Security Rule already identified transmission security as a required category of safeguards in the United States (HHS, 2003). Clinics that send STL files by unencrypted email are in conflict with that requirement today, not only under future rules.

2. Proposed Informatics Solution

Statement of the Solution

The proposed solution is a lightweight Python script that encrypts an STL file using AES-256-GCM encryption before it is sent to a laboratory. The clinic runs the script on the file, which produces an encrypted version that cannot be read without a matching key. The encrypted file is attached to the email as usual. The decryption key is delivered separately through a different channel, such as a text message or a secure messaging platform. When the laboratory receives the file, a companion decryption script restores it to its original state. The process adds less than one minute to the existing workflow and requires no new hardware or vendor contracts.

Justification

This solution was chosen because it fits directly into what clinics already do. Staff do not need to learn a new email system or portal. The script runs on any standard computer using free, open-source software. Training requires only a short set of written steps. Most importantly, the solution addresses the exact moment where the vulnerability exists: the point at which the file leaves the clinic's network.

Encryption is the standard method for protecting electronic protected health information in transit. The 2003 HIPAA Security Rule identified it as the primary technical safeguard for transmission security (HHS, 2003). The proposed 2026 revisions go further by making it a hard requirement with no exceptions. By adopting this solution now, a clinic meets the current intent of the law and will already be compliant when the new rule takes effect. This is a low-cost way to avoid a high-cost problem.

Supporting Arguments

AES-256-GCM is the encryption standard used by the U.S. federal government to protect classified information. It has been in active use for more than 20 years and has not been broken by any known method. The GCM mode provides two protections in a single step. It encrypts the file so it cannot be read, and it generates an authentication tag so the recipient can verify the file was not altered during transit.

Sending the key through a separate channel means that an attacker who intercepts the email still cannot open the file. They would need to intercept both the encrypted attachment and the separately delivered key at the same time. That is a significantly harder task. The solution is proven, practical, and directly tied to the regulatory standard that governs this data.

3. Information Needed to Validate the Solution

Statement of Required Information

Three types of information are needed to confirm the solution works as intended. The first is file integrity data, which means confirming that a file decrypted after encryption is byte-for-byte identical to the original. The second is processing time, which means measuring how long the script takes to encrypt and decrypt files of different sizes. The third is unreadability confirmation, which means verifying that an encrypted file cannot be opened or interpreted using standard software.

Justification

Each of these measures reflects a concern that clinic staff would reasonably raise before adopting any new tool. Staff will ask whether the encryption damages the file. They will ask whether it slows their work. They will ask whether it actually stops an attacker from reading the data. Addressing all three questions with real test data gives clinic administrators the evidence they need to say yes.

Supporting Arguments

File integrity is the most important measure. If encryption or decryption corrupts even one file, the laboratory cannot work with it and the clinic must resend the scan. SHA-256 hashing is the standard method used in security testing to confirm that two files are identical. It produces a unique fingerprint for each file, and any change to the file changes that fingerprint completely. Comparing the hash of the original file to the hash of the decrypted file confirms that no data was lost or altered.

Processing time matters because staff adoption depends on the tool not creating additional burden. A threshold of under five seconds per file is realistic and practical in a clinical setting. Dental STL files typically range from one to ten megabytes, and AES-256-GCM processes files of that size in well under one second on standard consumer hardware.

Unreadability testing closes the loop by confirming that the encrypted output cannot be interpreted by standard software. That is the first thing an attacker would try. If the test passes, the solution stops the most common form of unauthorized access.

4. Plan for Validating or Testing the Solution

Statement of the Validation Plan

The solution will be tested using a minimum of 30 to 50 STL files drawn from three categories. The first category is publicly available files from the NIH 3D Print Exchange and GrabCAD, which are realistic dental and anatomical scan files. The second category is synthetic files created to simulate edge cases, including very large files, files with complex geometry, and files that represent incomplete scans. The third category is standard-sized files that represent typical clinical output.

Each file will be encrypted using the script and then decrypted. Three values will be recorded for each file: the SHA-256 hash match result, the processing time in seconds, and the result of attempting to open the encrypted file with standard software.

Justification

Testing with 30 to 50 files is the right scale for this validation. It is large enough to produce reliable performance averages and to catch any inconsistency in the integrity check. It is small enough to complete in a reasonable amount of time without special equipment. Including edge cases ensures the solution does not fail under unusual conditions that could occur in real clinical use.

Supporting Arguments

The SHA-256 hash comparison will be automated using a Python verification script. This removes the possibility of human error in the comparison. Processing times will be recorded separately for three size categories: small files under one megabyte, medium files between one and five megabytes, and large files over five megabytes. This breakdown allows a precise analysis of performance across the range of files a clinic would actually send.

The unreadability test will attempt to open each encrypted file using three types of software: a standard text editor, a dedicated STL viewer, and a generic file explorer. If none of these can display the file content, the test is passed. Results for all files will be recorded in a spreadsheet for review and reporting.

Success Criteria

The solution passes validation when all three of the following conditions are met:

- One hundred percent of decrypted files produce a SHA-256 hash that matches the original file.

- The average processing time across all file sizes is under five seconds.

- Zero encrypted files can be opened or read by standard software without the decryption key.

5. Assessment of Hypothetical Results and Impact

Statement of Expected Results

The solution is expected to meet all three success criteria. All files should decrypt without data loss. Processing time should be well under five seconds for files of typical clinical size. No encrypted file should be readable without the decryption key. These outcomes are expected based on the known performance of AES-256-GCM encryption in comparable applications and on the documented capabilities of the Python cryptography library used to implement it.

Justification

AES-256 is not an experimental technology. It has been the federal encryption standard since 2001. It is used to protect financial transactions, classified government communications, and medical records in large health systems. The Python cryptography library that implements the script is maintained by a dedicated security team and is used in production by major technology organizations worldwide. There is no reasonable basis to expect it to fail on files of the size and type that dental clinics generate.

Impact on the Problem

If the solution performs as expected, the primary vulnerability in the dental clinic workflow is closed. Every STL file that leaves the clinic will be protected. A laboratory that receives an encrypted file and a separately delivered key can verify the file's integrity before opening it. An attacker who intercepts the email gets a file they cannot use.

The clinic would be in compliance with HIPAA transmission security requirements under the current rule and would already meet the mandatory encryption requirement when the 2026 revisions take effect. The clinic would also satisfy GDPR Article 5(1)(f)'s integrity and confidentiality principle, which requires appropriate technical measures to protect personal data, and would be better positioned to meet the 72-hour breach notification obligation under GDPR Article 33, since the use of encryption is a significant mitigating factor in breach assessments (European Parliament, 2016).

Broader Impact

This solution is not limited to dental clinics. Any small healthcare provider that transmits sensitive files by email faces the same vulnerability. The same script can be adapted for radiology images, pathology reports, and other clinical file types. The cost of adoption is near zero. The benefit to patients is concrete and lasting.

Recital 51 of GDPR states that personal data which are particularly sensitive in relation to fundamental rights and freedoms merit specific protection, because the context of their processing could create significant risks to those rights and freedoms (European Parliament, 2016). Biometric data is at the top of that category precisely because it cannot be changed once compromised. Preventing a breach with a free script and a one-minute workflow change is a straightforward decision. If a few hundred clinics adopt this approach, millions of patient records become safer. That outcome is worth the effort.

Required Compliance Actions for Dental Clinic
Requirement	Compliant Action
Secure Transmission	Use end-to-end encrypted platforms (e.g., 3Shape Communicate, lab portals). Never use plain email.
Data Processing Agreement	Sign a DPA with every dental lab before sending any scan data.
Access Controls	Ensure the lab can only access the specific case data needed.
Retention Limits	Require the lab to delete or return data after the case is complete.
Lawful Basis	Document that processing is necessary for dental treatment under Article 9(2)(h).
Patient Transparency	Inform patients in the privacy notice that scans are shared with labs.
Breach Plan	Maintain a 72-hour breach notification process as required by GDPR.

Conclusion

Dental clinics send unencrypted patient data through email every day. The data they send is biometric. It is permanent. It cannot be replaced if it is stolen. GDPR Article 9 places this category of data under the highest level of legal protection available, and GDPR Article 5(1)(f) requires that it be secured with appropriate technical measures during transmission. HIPAA's transmission security requirements point to the same standard. New rules expected in the United States in 2026 will make encryption mandatory with no exceptions.

A Python script using AES-256-GCM encryption solves this problem directly. It costs nothing to implement. It takes less than one minute to use. It protects the file from the moment it leaves the clinic to the moment it arrives at the laboratory. The validation plan described in this paper will confirm the tool works correctly before any clinic is asked to adopt it. The expected results are strong. The evidence base is solid.

There is no good reason to wait. The technology is proven. The regulatory deadline is approaching. Patients are at risk right now. Clinics that act today protect their patients and protect themselves. This solution should be approved and implemented immediately.





References
Centers for Medicare & Medicaid Services. (2007). Security 101 for covered entities (HIPAA Security Series). U.S. Department of Health and Human Services.

European Parliament & Council of the European Union. (2016). Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 on the protection of natural persons with regard to the processing of personal data (General Data Protection Regulation). Official Journal of the European Union.

IBM Security. (2024). Cost of a data breach report 2024. IBM Corporation.

UK Information Commissioner's Office. (2024). Biometric data guidance. ICO.

U.S. Department of Health and Human Services. (2003). Health insurance reform: Security standards; Final rule. 45 C.F.R. pts. 160, 162, and 164. Federal Register.

U.S. Department of Health and Human Services. (2025). HIPAA Security Rule to strengthen the cybersecurity of electronic protected health information. Office for Civil Rights.

Verizon. (2024). 2024 data breach investigations report. Verizon Business.
<img width="468" height="636" alt="image" src="https://github.com/user-attachments/assets/f5d4ed79-c6dc-4dca-824e-a474a72f2da0" />

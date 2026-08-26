E8_KNOWLEDGE = """# ASD Essential Eight Maturity Model - AI Assessment Knowledge Base

Source: https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/essential-eight/essential-eight-maturity-model
Additional ASD assessment artifacts used as methodology references:
- Essential Eight assessment report template (November 2023)
- Example Essential Eight assessment test plan - Maturity Level One (August 2024)
- Example Essential Eight assessment test plan - Maturity Level Two (November 2023)
- Example Essential Eight assessment test plan - Maturity Level Three (November 2023)
Source date: Essential Eight maturity model, November 2023; cyber.gov.au page last updated 27 Nov 2023.
Use note: This is a paraphrased operational summary for AI-assisted evidence review. It is not official certification text.

Global assessment principles:
- Assess only the submitted evidence. Do not invent implementation details.
- Policy text is weak evidence: it can show intent, ownership, or stated procedure, but it does not prove implementation.
- Stronger evidence includes tool exports, configuration screenshots, logs, test records, vulnerability scans, patch registers, access control exports, conditional access policies, backup job reports, and change records.
- If a requirement is not evidenced, mark it as a gap or ask a clarification question. Prefer "Insufficient Evidence" over a hallucinated compliance claim.
- ML0 means the submitted evidence does not support Maturity Level One, or important requirements are missing, ineffective, or not evidenced.
- ML1 focuses on defending against common commodity tradecraft.
- ML2 adds stronger controls against more deliberate adversaries.
- ML3 adds hardened, comprehensive, and more resilient implementation expectations.

Assessment report and test-plan guidance:
- A credible assessment report should include background, scope, approach, limitations, detailed findings for each Essential Eight strategy, a summary of recommendations, and an evidence appendix.
- Findings should explain whether the target maturity requirements were achieved, how the requirement was tested, how it was implemented or not implemented, and why the outcome was reached.
- Implementation status should be treated as evidence-based, using categories such as effective, not effective, alternate control, not applicable, not implemented, or not assessed.
- A test plan should connect each requirement to a test method and test finding. Common methods include reviewing configuration exports, requesting historical evidence, observing a control in operation, comparing timestamps to required timeframes, sampling scoped systems, and checking whether tool output matches the declared system boundary.
- Always call out assessment limitations, such as missing evidence, incomplete scope, unavailable tools, sample-size constraints, or inability to perform technical testing.
- For uploaded URLs, do not assume the linked document has been fetched. Unless the content is actually provided, treat the URL as a reference only and ask the user to upload or paste the document contents.
- Recommendations should be practical and evidence-oriented: state the action, the priority, the reason, and the specific evidence that would close the gap.
- For hackathon demo output, show the top gaps and recommendations, but preserve traceability in the JSON response for future report generation.

## Patch Applications

Assessment intent:
Confirm that applications are discovered, vulnerability-scanned, patched, and unsupported software is removed in timeframes appropriate to risk.

ML0 meaning:
No reliable application inventory, vulnerability scanning, patching process, or evidence of timely remediation is provided.

ML1 requirement summary:
Maintain automated discovery of assets and application exposure. Use an up-to-date vulnerability scanner. Scan internet-facing services frequently and scan high-risk user applications such as office suites, browsers, email clients, PDF software, and security products at least weekly. Patch critical or exploit-available vulnerabilities in internet-facing services rapidly, and patch other application vulnerabilities within defined timeframes. Remove unsupported high-risk applications.

ML2 requirement summary:
Extend scanning and patching coverage to broader application sets, not only internet-facing and high-risk user applications. Evidence should show repeatable scanning, prioritisation, and remediation within defined windows.

ML3 requirement summary:
Apply tighter timelines to high-risk application categories when vulnerabilities are critical or exploit-available. Remove unsupported applications across the environment and maintain stronger evidence of ongoing enforcement.

Strong evidence examples:
Vulnerability scanner reports, patch register, asset inventory, software inventory, change tickets, deployment logs, endpoint management exports, exception register.

Weak evidence examples:
General policy statements such as "applications are patched regularly" without dates, systems, scan results, or remediation evidence.

Common gaps to detect:
No application inventory; no vulnerability scans; unclear patch timeframes; no evidence for exploit-available vulnerabilities; unsupported software remains; exceptions are undocumented.

Clarification questions to ask:
Which scanner is used? How often are user applications scanned? What is the SLA for critical or exploit-available vulnerabilities? Which unsupported applications remain and why?

Recommended evidence to upload:
Recent vulnerability scan, patch compliance report, application inventory, unsupported software report, remediation ticket sample.

## Patch Operating Systems

Assessment intent:
Confirm that operating systems, firmware, drivers, and internet-facing services are identified, vulnerability-scanned, patched, and unsupported platforms are removed.

ML0 meaning:
No reliable operating system inventory, scan output, patch cadence, or remediation evidence is provided.

ML1 requirement summary:
Maintain asset discovery and vulnerability scanning for operating systems and internet-facing services. Patch critical or exploit-available vulnerabilities in internet-facing services rapidly. Patch other operating system vulnerabilities within defined timeframes. Remove unsupported operating systems and internet-facing services where practical.

ML2 requirement summary:
Broaden coverage and strengthen timeframes for workstations, servers, and other operating systems. Evidence should show vulnerability identification, prioritisation, patch deployment, and exception handling.

ML3 requirement summary:
Apply mature and consistently enforced patch management across all supported operating systems, with faster remediation for critical or exploit-available vulnerabilities and no unsupported operating systems unless formally risk-managed.

Strong evidence examples:
Endpoint management compliance reports, server patch reports, vulnerability scans, asset inventory, OS version exports, change records, exception approvals.

Weak evidence examples:
Patch policy text, maintenance window descriptions, or informal statements without scan or deployment evidence.

Common gaps to detect:
No OS inventory; unsupported systems present; missing internet-facing scan evidence; unclear critical patch SLA; no exception register; no proof of successful deployment.

Clarification questions to ask:
Which systems are in scope? How often are operating systems scanned? How quickly are critical or exploit-available vulnerabilities remediated? Are unsupported systems present?

Recommended evidence to upload:
OS inventory, vulnerability scan report, patch compliance dashboard, deployment logs, exception register.

## Multi-factor Authentication

Assessment intent:
Confirm that MFA is enforced for privileged and non-privileged users in the required contexts, with stronger phishing-resistant factors as maturity increases.

ML0 meaning:
MFA is absent, optional, inconsistently enforced, or not evidenced for required accounts and services.

ML1 requirement summary:
Require MFA for users accessing internet-facing services, especially privileged accounts and important services. MFA should use at least two factors and should not rely on weak single-factor substitutes. Successful and failed authentication events should be logged.

ML2 requirement summary:
Extend MFA coverage to important data repositories and additional business-critical access paths. Prefer stronger possession-based factors and reduce reliance on easily intercepted methods.

ML3 requirement summary:
Enforce MFA broadly for access to systems, applications, and data repositories. Use phishing-resistant MFA where required, such as FIDO2/WebAuthn, smart cards, or certificate-based authentication.

Strong evidence examples:
Entra ID Conditional Access exports, identity provider policy exports, MFA registration reports, sign-in logs, privileged account policy screenshots, exception reports.

Weak evidence examples:
Text saying "MFA is enabled" without scope, target users, policy state, exclusions, or logs.

Common gaps to detect:
MFA not enforced for all required accounts; privileged users excluded; legacy authentication allowed; weak factors used; no logs; broad exception groups; no evidence for important repositories.

Clarification questions to ask:
Which users and apps are covered? Are privileged accounts included? Are there exclusions? Are phishing-resistant methods required for high-risk access? Are legacy protocols blocked?

Recommended evidence to upload:
Conditional Access policy export, MFA method report, sign-in logs, privileged user group list, exception list.

## Restrict Administrative Privileges

Assessment intent:
Confirm that privileged access is limited, separated, monitored, and used only for administrative tasks.

ML0 meaning:
Administrative access is broad, undocumented, mixed with standard user activity, or not evidenced.

ML1 requirement summary:
Privileged access is limited to authorised users. Admin accounts are separate from standard accounts, are used only for admin tasks, and are not used for email or web browsing. Privileged events are logged and reviewed.

ML2 requirement summary:
Strengthen privileged access controls with tighter authorisation, reduced standing privilege, better credential management, MFA for privileged access paths, and stronger monitoring.

ML3 requirement summary:
Enforce mature privileged access management, such as just-in-time or just-enough access, strong MFA, session controls, and timely review/removal of privileges.

Strong evidence examples:
AD/Azure AD privileged group exports, PAM/PIM configuration, admin account inventory, privileged access logs, approval records, access review records.

Weak evidence examples:
Policy saying "admin access is restricted" without group membership, approvals, reviews, or logs.

Common gaps to detect:
Shared admin accounts; standard accounts with admin rights; no access review; no MFA for admin actions; no logs; admin accounts used for email or web; stale privileged users.

Clarification questions to ask:
Who has privileged access? How is it approved? Are admin accounts separate? Is access time-bound? Are privileged events logged and reviewed?

Recommended evidence to upload:
Privileged group export, PIM/PAM screenshots, admin account list, access review report, privileged sign-in logs.

## Application Control

Assessment intent:
Confirm that only approved executables, software libraries, scripts, installers, and other active content can run on relevant systems.

ML0 meaning:
No enforceable allow-listing or application control evidence is provided, or users can run unapproved code.

ML1 requirement summary:
Implement application control on workstations for executables, software libraries, scripts, installers, compiled HTML, HTML applications, and control panel applets. Rules should be actively enforced and maintained.

ML2 requirement summary:
Extend application control coverage, improve rule quality, and reduce bypass opportunities. Rules should cover common user-writable paths and script execution paths.

ML3 requirement summary:
Apply mature application control across workstations and servers where required, with central management, logging, regular review, and protection against tampering.

Strong evidence examples:
WDAC/AppLocker policy export, application control console screenshots, blocked execution logs, allow-list rules, deployment scope report, exception register.

Weak evidence examples:
Policy text claiming only approved software is allowed without enforced configuration or event logs.

Common gaps to detect:
Audit mode only; incomplete file type coverage; users can run scripts from writable paths; no server coverage; no logging; no exception process; local admins can disable controls.

Clarification questions to ask:
Which application control technology is used? Is it enforced or audit-only? Which file types are covered? What systems are in scope? How are exceptions approved?

Recommended evidence to upload:
Application control policy export, enforcement mode screenshot, event logs, scope/deployment report, exception register.

## Restrict Microsoft Office Macros

Assessment intent:
Confirm that Office macros from the internet are blocked, only trusted macros can run, and users cannot weaken macro security settings.

ML0 meaning:
Macros can run broadly, users can change macro settings, or there is no evidence of macro control.

ML1 requirement summary:
Block macros from the internet and restrict macro execution to trusted locations, trusted documents, or authorised business use. Users should not be able to change macro security settings.

ML2 requirement summary:
Strengthen controls for macro execution, limit who can run approved macros, and require stronger validation or signing for trusted macros.

ML3 requirement summary:
Apply strict macro controls across the environment, with signed and approved macros only, central enforcement, logging, and limited exceptions.

Strong evidence examples:
Group Policy exports, Intune policy screenshots, Office security baseline settings, macro block logs, trusted location configuration, exception register.

Weak evidence examples:
User guidance telling staff not to enable macros, without technical enforcement.

Common gaps to detect:
Macros from internet not blocked; users can change settings; unsigned macros allowed; trusted locations too broad; no logging; no exception approval.

Clarification questions to ask:
Are internet-origin macros blocked? Can users change macro settings? Are trusted macros signed? Which users or business units have exceptions?

Recommended evidence to upload:
Office macro policy export, GPO/Intune settings, macro event logs, trusted location list, exception approval record.

## User Application Hardening

Assessment intent:
Confirm that common user applications are hardened to reduce exploitation through browsers, Office, PDF readers, Java, scripting engines, and legacy components.

ML0 meaning:
User applications keep risky features enabled, users can weaken settings, or no hardening evidence is provided.

ML1 requirement summary:
Disable or remove Internet Explorer 11. Disable or restrict risky features in web browsers, Office, PDF software, Java, and scripting where not required. Users should not be able to change security settings that reduce protection.

ML2 requirement summary:
Strengthen hardening across more applications and enforce settings centrally. Reduce attack surface from ads, browser plugins, scripting, and untrusted content handling.

ML3 requirement summary:
Maintain mature, centrally enforced hardening baselines with monitoring, exception management, and limited ability for users or local admins to weaken controls.

Strong evidence examples:
Security baseline exports, GPO/Intune configuration, browser policy export, Office/PDF hardening settings, endpoint configuration reports, compliance dashboard.

Weak evidence examples:
Policy or awareness material telling users to avoid risky content without enforced settings.

Common gaps to detect:
IE11 present; users can change application security settings; browser plugins allowed broadly; Office/PDF risky features enabled; no central baseline; no exception tracking.

Clarification questions to ask:
Which hardening baseline is applied? Are settings enforced centrally? Can users override them? Which browsers, Office apps, PDF readers, and Java runtimes are in scope?

Recommended evidence to upload:
GPO/Intune hardening export, browser policy export, Office/PDF security settings, compliance report, exception list.

## Regular Backups

Assessment intent:
Confirm that backups of important data, applications, and settings are performed, protected, retained, and tested so systems can be restored after destructive or disruptive events.

ML0 meaning:
Backups are not evidenced, are incomplete, are not protected, are not retained appropriately, or restore testing is missing.

ML1 requirement summary:
Backups of important data, applications, and settings are performed and retained in line with business criticality and continuity requirements. Backups should support restoration to a common point in time where needed. Backups are retained in a secure and resilient manner. Restoration is tested as part of disaster recovery exercises.

ML2 requirement summary:
Add access controls so unprivileged accounts cannot access backups belonging to other accounts or systems, and cannot modify or delete backups. Privileged user accounts, excluding backup administrator accounts, are prevented from modifying and deleting backups.

ML3 requirement summary:
Add stronger protection for backup administrator accounts so they are prevented from modifying and deleting backups during the retention period. Backup protection should be resilient against compromise of ordinary and privileged accounts.

Strong evidence examples:
Backup job export, backup schedule, retention configuration, restore test record, disaster recovery exercise report, immutable storage setting, backup vault access control export, backup administrator role configuration.

Weak evidence examples:
Short policy statements such as "weekly backups are performed" or "IT owns backups" without backup tool output, retention settings, restore results, access controls, or protected storage evidence.

Common gaps to detect:
No retention period; no restore testing schedule or result; no evidence of secure and resilient storage; no proof of common point-in-time restore; no immutable/protected backup control; no account restrictions for unprivileged users, privileged users, or backup administrators; no technical backup system evidence; no list of critical systems covered.

Clarification questions to ask:
Which data, applications, and settings are backed up? What is the retention period? Can systems be restored to a common point in time? When was the latest restore test? Are backups immutable or otherwise protected? Which accounts can read, modify, or delete backups? Are backup administrator accounts restricted during retention?

Recommended evidence to upload:
Backup configuration export, backup job history, restore test record, DR exercise report, retention policy configuration, immutable storage screenshot, backup vault ACL export, backup administrator role export, critical systems coverage list.
"""

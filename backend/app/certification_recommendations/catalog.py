"""Versioned editorial catalogue, not a live certification marketplace.

URL checks were attempted with webfetch on 2026-10-10. A successful fetch
confirms page identity only, never price, eligibility, or current availability.
Technology labels are explicit exact-match coverage, not role-based inference.
"""
from dataclasses import dataclass


CATALOG_VERSION = "curated-certifications-v1"
CHECKED_ON = "2026-10-10"


@dataclass(frozen=True)
class CertificationDefinition:
    key: str
    name: str
    provider: str
    category: str
    skills: tuple[str, ...]
    official_url: str
    name_aliases: tuple[str, ...] = ()
    provider_aliases: tuple[str, ...] = ()
    verification_status: str = "OFFICIAL_PAGE_RETRIEVED"

    def provenance(self) -> dict:
        return {
            "source": "CURATED_OFFICIAL_PROVIDER_CATALOG",
            "catalog_version": CATALOG_VERSION,
            "source_url": self.official_url,
            "url_checked_on": CHECKED_ON,
            "verification_status": self.verification_status,
            "verification_note": (
                "Official page retrieved; identity and topic reviewed only."
                if self.verification_status == "OFFICIAL_PAGE_RETRIEVED"
                else "Official-domain URL fetch returned HTTP 403; page content could not be verified."
            ),
            "coverage_basis": "Editorial exact technology labels; not a complete exam syllabus.",
            "limitations": "Prices, availability, prerequisites and eligibility are not live verified. Check the provider.",
        }


CATALOG = (
    CertificationDefinition(
        "python-institute-pcap", "PCAP - Certified Associate Python Programmer",
        "Python Institute", "Programming", ("Python",),
        "https://pythoninstitute.org/pcap",
        ("PCAP", "PCAP - Certified Associate in Python Programming", "Certified Associate Python Programmer"),
        ("OpenEDG Python Institute",),
    ),
    CertificationDefinition(
        "oracle-java-se-17-developer", "Oracle Certified Professional: Java SE 17 Developer",
        "Oracle", "Programming", ("Java",),
        "https://education.oracle.com/java-se-17-developer/pexam_1Z0-829",
        ("Oracle Certified Professional Java SE 17 Developer",),
        ("Oracle University",), "FETCH_BLOCKED_HTTP_403",
    ),
    CertificationDefinition(
        "oracle-database-sql", "Oracle Database SQL Certified Associate",
        "Oracle", "Databases", ("SQL",),
        "https://education.oracle.com/oracle-database-sql/pexam_1Z0-071",
        (), ("Oracle University",), "FETCH_BLOCKED_HTTP_403",
    ),
    CertificationDefinition(
        "linux-foundation-cka", "Certified Kubernetes Administrator (CKA)",
        "The Linux Foundation", "Cloud and Containers", ("Kubernetes",),
        "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
        ("CKA", "Certified Kubernetes Administrator"),
        ("Linux Foundation", "CNCF", "Cloud Native Computing Foundation"),
    ),
    CertificationDefinition(
        "microsoft-azure-fundamentals", "Microsoft Certified: Azure Fundamentals",
        "Microsoft", "Cloud", ("Microsoft Azure", "Azure"),
        "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/",
        ("Azure Fundamentals", "AZ-900"), ("Microsoft Learn",),
    ),
    CertificationDefinition(
        "aws-cloud-practitioner", "AWS Certified Cloud Practitioner",
        "Amazon Web Services", "Cloud", ("Amazon Web Services AWS", "Amazon Web Services", "AWS"),
        "https://aws.amazon.com/certification/certified-cloud-practitioner/",
        ("AWS Cloud Practitioner",), ("AWS", "Amazon Web Services (AWS)"),
    ),
    CertificationDefinition(
        "microsoft-power-bi-data-analyst", "Microsoft Certified: Power BI Data Analyst Associate",
        "Microsoft", "Data Analytics", ("Microsoft Power BI", "Power BI"),
        "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/",
        ("Power BI Data Analyst Associate", "PL-300"), ("Microsoft Learn",),
    ),
)

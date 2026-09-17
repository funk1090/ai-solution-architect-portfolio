"""Domain-specific synthetic data provider.

Wraps Faker so that every generator draws fictional business entities
(companies, project names, requirements) from a single, consistently
seeded source — this is what makes NFR1 (reproducibility) possible.
"""
from faker import Faker

_REQUIREMENT_CATEGORIES = [
    "Reliability",
    "Security",
    "Performance",
    "Usability",
    "Compliance",
    "Integration",
    "Scalability",
    "Maintainability",
]

_REQUIREMENT_PRIORITIES = ["Critical", "High", "Medium", "Low"]

# ADR-0004: category- and priority-specific vocabulary used by
# correlated_requirement() to give a classifier a genuinely learnable
# (but not trivial) signal between requirement text and its labels.
_CATEGORY_VOCAB: dict[str, list[str]] = {
    "Reliability": [
        "99.99% uptime guarantees",
        "automatic failover between redundant nodes",
        "graceful degradation under partial outages",
        "self-healing infrastructure components",
    ],
    "Security": [
        "end-to-end encryption of data in transit",
        "multi-factor authentication for all users",
        "role-based access control across all modules",
        "continuous vulnerability scanning",
    ],
    "Performance": [
        "sub-second response times under peak load",
        "high-throughput batch processing",
        "low-latency access to frequently used data",
        "efficient caching of repeated queries",
    ],
    "Usability": [
        "an intuitive interface requiring minimal training",
        "accessible design compliant with WCAG guidelines",
        "a streamlined onboarding experience for new users",
        "consistent navigation across all screens",
    ],
    "Compliance": [
        "GDPR-compliant handling of personal data",
        "SOC 2 Type II certification of all data stores",
        "complete regulatory audit trails",
        "configurable data residency by region",
    ],
    "Integration": [
        "seamless integration with existing enterprise APIs",
        "standardized data exchange formats",
        "compatibility with legacy backend systems",
        "real-time synchronization across connected systems",
    ],
    "Scalability": [
        "elastic scaling of compute resources on demand",
        "support for a rapidly growing user base",
        "a horizontally distributed processing architecture",
        "cloud-native scalability across regions",
    ],
    "Maintainability": [
        "a well-documented and modular codebase",
        "automated test coverage above 80%",
        "clear semantic versioning of all releases",
        "straightforward troubleshooting via structured logs",
    ],
}

_PRIORITY_VOCAB: dict[str, list[str]] = {
    "Critical": [
        "is mission-critical and must be delivered immediately",
        "is required for regulatory compliance and cannot be delayed",
        "poses a significant business risk if left unaddressed",
    ],
    "High": [
        "is a high priority for the upcoming release",
        "significantly impacts core business operations",
        "should be addressed as soon as possible",
    ],
    "Medium": [
        "is important but can be scheduled for a future release",
        "provides meaningful value without blocking other work",
        "should be planned within the next few sprints",
    ],
    "Low": [
        "would be a nice-to-have enhancement",
        "can be deferred without significant impact",
        "is a low-priority improvement for future consideration",
    ],
}

# Probability that the vocabulary used does NOT match the assigned
# label -- deliberate noise so the classification problem in Phase 3
# is learnable but not a trivial keyword lookup (ADR-0004).
_LABEL_NOISE_PROBABILITY = 0.15

_PRODUCT_KINDS = ["Router", "Switch", "Gateway", "Controller", "Module"]

_SPECIFICATION_LABELS = [
    "Operating Temperature",
    "Power Consumption",
    "Dimensions",
    "Weight",
    "Input Voltage",
    "Network Interfaces",
    "Storage Capacity",
    "Operating Humidity",
]

_SPECIFICATION_UNITS = ["W", "V", "mm", "kg", "GB", "ports", "%"]


class EnterpriseFakerProvider:
    def __init__(self, seed: int) -> None:
        self._faker = Faker()
        self._faker.seed_instance(seed)

    def company_name(self) -> str:
        return self._faker.company()

    def project_name(self) -> str:
        return f"{self._faker.bs().title()} Modernization Initiative"

    def budget_range_usd(self) -> tuple[int, int]:
        low = self._faker.random_int(min=50_000, max=500_000, step=10_000)
        high = low + self._faker.random_int(min=50_000, max=300_000, step=10_000)
        return low, high

    def technical_requirement(self) -> str:
        return f"The solution shall provide {self._faker.catch_phrase().lower()}."

    def requirement_category(self) -> str:
        return self._faker.random_element(_REQUIREMENT_CATEGORIES)

    def requirement_priority(self) -> str:
        return self._faker.random_element(_REQUIREMENT_PRIORITIES)

    def requirement_id(self, index: int) -> str:
        return f"REQ-{index:04d}"

    def correlated_requirement(self, category: str, priority: str) -> str:
        """Generates requirement text correlated with its Category and
        Priority labels, with controlled noise (ADR-0004). Used only by
        ExcelRequirementsGenerator, which trains Phase 3's classifier on
        this data -- technical_requirement() above remains unchanged
        for RFPGenerator/TechnicalManualGenerator, which have no
        category/priority to correlate against.
        """
        if self._faker.random.random() < _LABEL_NOISE_PROBABILITY:
            category_phrase = self._faker.random_element(
                [phrase for phrases in _CATEGORY_VOCAB.values() for phrase in phrases]
            )
        else:
            category_phrase = self._faker.random_element(_CATEGORY_VOCAB[category])

        if self._faker.random.random() < _LABEL_NOISE_PROBABILITY:
            priority_phrase = self._faker.random_element(
                [phrase for phrases in _PRIORITY_VOCAB.values() for phrase in phrases]
            )
        else:
            priority_phrase = self._faker.random_element(_PRIORITY_VOCAB[priority])

        return (
            f"The solution shall provide {category_phrase}. "
            f"This requirement {priority_phrase}."
        )

    def product_name(self) -> str:
        kind = self._faker.random_element(_PRODUCT_KINDS)
        return f"{self._faker.word().capitalize()}-{kind}-{self._faker.random_int(100, 999)}"

    def version_number(self) -> str:
        return f"{self._faker.random_int(1, 5)}.{self._faker.random_int(0, 9)}"

    def specification_item(self) -> tuple[str, str]:
        label = self._faker.random_element(_SPECIFICATION_LABELS)
        unit = self._faker.random_element(_SPECIFICATION_UNITS)
        value = f"{self._faker.random_int(1, 500)} {unit}"
        return label, value

    def procedure_step(self) -> str:
        return self._faker.sentence(nb_words=10)

    def paragraph(self, sentence_count: int = 5) -> str:
        return self._faker.paragraph(nb_sentences=sentence_count)

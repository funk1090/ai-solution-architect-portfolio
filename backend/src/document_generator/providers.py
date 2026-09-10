"""Domain-specific synthetic data provider.

Wraps Faker so that every generator draws fictional business entities
(companies, project names, requirements) from a single, consistently
seeded source — this is what makes NFR1 (reproducibility) possible.
"""
from faker import Faker


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

    def paragraph(self, sentence_count: int = 5) -> str:
        return self._faker.paragraph(nb_sentences=sentence_count)

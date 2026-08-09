"""
BridgeLab Toolkit
Generator Validator
"""

from __future__ import annotations

from core.models import Issue


class GeneratorValidator:
    """
    Validates generated Markdown documents.
    """

    # =========================================================
    # Validate
    # =========================================================

    def validate(
        self,
        name: str,
        content: str,
    ) -> list[Issue]:

        issues: list[Issue] = []

        # -----------------------------------------------------
        # Empty document
        # -----------------------------------------------------

        if not content.strip():

            issues.append(

                Issue(

                    severity="Error",

                    article=name,

                    category="Generator",

                    message="Generated document is empty",

                )

            )

            return issues

        lines = content.splitlines()

        # -----------------------------------------------------
        # Missing title
        # -----------------------------------------------------

        if not lines[0].startswith("# "):

            issues.append(

                Issue(

                    severity="Error",

                    article=name,

                    category="Generator",

                    message="Document does not begin with a level-1 heading",

                )

            )

        # -----------------------------------------------------
        # Duplicate headings
        # -----------------------------------------------------

        headings = set()

        for line in lines:

            if line.startswith("#"):

                if line in headings:

                    issues.append(

                        Issue(

                            severity="Warning",

                            article=name,

                            category="Generator",

                            message=f"Duplicate heading: {line}",

                        )

                    )

                headings.add(line)

        return issues

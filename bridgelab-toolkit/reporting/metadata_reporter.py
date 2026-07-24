"""
BridgeLab Toolkit
Metadata Reporter
"""

from __future__ import annotations

from .base_reporter import BaseReporter


class MetadataReporter(BaseReporter):
    """
    Reports metadata validation results.
    """

    def __init__(self):

        super().__init__(

            title="Metadata Validation"

        )

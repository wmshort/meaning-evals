"""The exceptions the harness raises at its module boundaries.

The command line reports any `MeaningEvalsError` as a one-line message and exits non-zero;
anything else is a defect and propagates with its traceback.
"""


class MeaningEvalsError(Exception):
    """Base class for failures the command line reports without a traceback."""


class ConfigError(MeaningEvalsError):
    """The configuration file or a prompt template is missing or invalid."""


class MissingKeyError(ConfigError):
    """An API key the command needs is not set in the environment."""


class DataError(MeaningEvalsError):
    """A data file is missing, malformed, or inconsistent with another data file."""


class ProviderError(MeaningEvalsError):
    """A provider call failed after its bounded retries, or returned no usable metadata."""


class GenerationError(MeaningEvalsError):
    """The generator returned an answer that cannot be used as an item."""

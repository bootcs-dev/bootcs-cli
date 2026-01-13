"""
BootCS CLI - Check and submit your code

基于 check50/lib50 重写，适配 bootcs API
"""

__version__ = "2.0.0"

# 导出 check API (对齐 check50)
from .check import (
    Failure,
    Mismatch,
    Missing,
    data,
    exists,
    hash,
    import_checks,
    include,
    log,
    regex,
    run,
)
from .check.runner import check

__all__ = [
    "exists",
    "hash",
    "include",
    "run",
    "log",
    "data",
    "import_checks",
    "regex",
    "check",
    "Failure",
    "Mismatch",
    "Missing",
]

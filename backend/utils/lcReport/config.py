"""
ETL 配置类 — 从原 huili/惠理基金/src/etl_excel/config.py 迁移
控制 Excel 解析行为的参数集合。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Set


@dataclass(frozen=True)
class EtlConfig:
    # 表头锚点文本（定位真实数据开始的行）
    header_anchor: str = "Group/Investment"
    # 向上探测合并表头时，最多向上扫几行
    max_header_depth: int = 5
    # 占位符：这些值在数据清洗时转为 NA
    placeholder_tokens: Set[str] = field(
        default_factory=lambda: {"", "-"}
    )
    # 分组标题行黑名单关键字（含这些词的行不视为分组标题）
    group_blacklist_keywords: Set[str] = field(
        default_factory=lambda: {
            "Benchmark",
            "Peer Group Average",
            "Peer Group Count",
            "Group/Investment",
        }
    )
    # 行类型关键字映射（用于识别辅助行）
    row_type_keywords: Dict[str, str] = field(
        default_factory=lambda: {
            "Benchmark": "Benchmark",
            "Peer Group Average": "Peer_Avg",
            "Peer Group Count": "Peer_Count",
        }
    )
    # 非首列填充比例阈值：若超过该比例，则视为数据行而非分组标题
    non_first_col_fill_ratio_threshold: float = 0.05
    # Quartile_weekly 导入时只处理以下 Sheet（空集表示不过滤）
    qw_target_sheets: FrozenSet[str] = frozenset({
        "VP_PG_HKSFC funds_t-1_inc",
        "VP_PG_Offshore funds_t-1_Inc",
        "VP_PG_UCITS Funds_t-1_Inc",
        "RF_fund performance_t-1",
    })
    # 必须存在的列标识
    required_columns: List[str] = field(
        default_factory=lambda: [
            "Group/Investment",
            "ISIN",
        ]
    )
    # 是否开启严格模式（严格模式下数据质量问题会抛出异常）
    strict_mode: bool = True
    quality_min_group_per_sheet: int = 1
    quality_min_fund_rows_per_sheet: int = 1
    max_error_samples: int = 30


@dataclass(frozen=True)
class PipelineArgs:
    input_path: Path
    output_dir: Path
    mode: str = "strict"

    def validate(self) -> None:
        if not self.input_path.exists():
            raise FileNotFoundError(
                f"[E1001] input file not found: {self.input_path.as_posix()}"
            )
        if self.mode not in {"strict", "lenient"}:
            raise ValueError(f"[E1002] unsupported mode: {self.mode}")

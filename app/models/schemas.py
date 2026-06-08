"""Pydantic 数据模型"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ExamType(str, Enum):
    """高考模式"""
    NEW_3_PLUS_1_PLUS_2 = "3+1+2"
    NEW_3_PLUS_3 = "3+3"
    TRADITIONAL = "传统文理"


class SubjectCategory(str, Enum):
    """科类"""
    PHYSICS = "物理类"  # 3+1+2 选物理
    HISTORY = "历史类"  # 3+1+2 选历史
    SCIENCE = "理科"    # 传统理科
    LIBERAL = "文科"    # 传统文科
    COMPREHENSIVE = "综合"  # 3+3 不分文理


class RecommendLevel(str, Enum):
    """推荐等级"""
    CHONG = "冲"   # 冲刺
    WEN = "稳"    # 稳妥
    BAO = "保"    # 保底


class StudentProfile(BaseModel):
    """考生画像"""
    province: str = Field(..., description="省份，如'河北'")
    score: int = Field(..., ge=0, le=750, description="高考分数")
    rank: Optional[int] = Field(None, ge=1, description="省排名/位次")
    exam_type: ExamType = Field(..., description="高考模式")
    subject_category: SubjectCategory = Field(..., description="科类")
    subjects: Optional[list[str]] = Field(None, description="选科组合，如['物理','化学','生物']")
    year: int = Field(default=2025, description="参考年份")
    preferred_cities: Optional[list[str]] = Field(None, description="意向城市")
    preferred_majors: Optional[list[str]] = Field(None, description="意向专业方向")
    avoid_majors: Optional[list[str]] = Field(None, description="排除专业")


class CollegeInfo(BaseModel):
    """院校信息"""
    college_id: str
    name: str
    province: str
    city: str
    level: str = Field(description="层次：985/211/双一流/普通本科")
    category: str = Field(description="类型：综合/理工/师范/医药等")
    is_985: bool = False
    is_211: bool = False
    is_double_first_class: bool = False


class AdmissionRecord(BaseModel):
    """录取记录"""
    year: int
    college_name: str
    major_name: str
    province: str
    subject_category: str
    min_score: int = Field(description="最低录取分")
    avg_score: Optional[int] = Field(None, description="平均录取分")
    min_rank: Optional[int] = Field(None, description="最低位次")
    plan_count: Optional[int] = Field(None, description="招生计划人数")
    batch: str = Field(default="本科批", description="录取批次")


class RecommendItem(BaseModel):
    """推荐结果项"""
    college_name: str
    major_name: str
    level: RecommendLevel
    probability: float = Field(ge=0, le=1, description="录取概率估算")
    reason: str = Field(description="推荐理由")
    historical_min_score: Optional[int] = None
    historical_min_rank: Optional[int] = None
    score_diff: Optional[int] = Field(None, description="与考生分数的差值")


class AgentState(BaseModel):
    """Agent 对话状态"""
    student_profile: Optional[StudentProfile] = None
    collected_info: dict = Field(default_factory=dict, description="已收集的信息片段")
    recommendations: list[RecommendItem] = Field(default_factory=list)
    conversation_summary: str = ""

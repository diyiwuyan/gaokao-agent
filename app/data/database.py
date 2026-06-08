"""SQLite 数据库管理"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from app.config import DB_PATH


def get_db_path() -> str:
    """确保数据库目录存在并返回路径"""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


@contextmanager
def get_connection():
    """获取数据库连接上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_connection() as conn:
        conn.executescript("""
        -- 院校信息表
        CREATE TABLE IF NOT EXISTS colleges (
            college_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            province TEXT,
            city TEXT,
            level TEXT,          -- 985/211/双一流/普通本科
            category TEXT,       -- 综合/理工/师范等
            is_985 INTEGER DEFAULT 0,
            is_211 INTEGER DEFAULT 0,
            is_double_first_class INTEGER DEFAULT 0,
            official_site TEXT,
            phone TEXT,
            address TEXT,
            intro TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 专业信息表
        CREATE TABLE IF NOT EXISTS majors (
            major_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,       -- 学科门类
            level TEXT,          -- 本科/专科
            duration INTEGER DEFAULT 4,
            description TEXT
        );

        -- 院校专业关联表
        CREATE TABLE IF NOT EXISTS college_majors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id TEXT NOT NULL,
            major_id TEXT NOT NULL,
            is_key_major INTEGER DEFAULT 0,  -- 是否重点学科
            FOREIGN KEY (college_id) REFERENCES colleges(college_id),
            FOREIGN KEY (major_id) REFERENCES majors(major_id),
            UNIQUE(college_id, major_id)
        );

        -- 历年录取分数线（核心表）
        CREATE TABLE IF NOT EXISTS admission_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            college_id TEXT NOT NULL,
            college_name TEXT NOT NULL,
            major_name TEXT,
            province TEXT NOT NULL,       -- 招生省份
            subject_category TEXT,        -- 物理类/历史类/理科/文科
            batch TEXT DEFAULT '本科批',   -- 录取批次
            min_score INTEGER,            -- 最低分
            avg_score INTEGER,            -- 平均分
            max_score INTEGER,            -- 最高分
            min_rank INTEGER,             -- 最低位次
            plan_count INTEGER,           -- 计划招生数
            actual_count INTEGER,         -- 实际录取数
            FOREIGN KEY (college_id) REFERENCES colleges(college_id)
        );

        -- 省控线/批次线
        CREATE TABLE IF NOT EXISTS province_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            province TEXT NOT NULL,
            subject_category TEXT,
            batch TEXT,
            score INTEGER NOT NULL,
            UNIQUE(year, province, subject_category, batch)
        );

        -- 一分一段表（位次表）
        CREATE TABLE IF NOT EXISTS score_rank_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            province TEXT NOT NULL,
            subject_category TEXT,
            score INTEGER NOT NULL,
            rank_number INTEGER NOT NULL,  -- 累计人数（位次）
            same_score_count INTEGER,      -- 同分人数
            UNIQUE(year, province, subject_category, score)
        );

        -- 招生计划表
        CREATE TABLE IF NOT EXISTS enrollment_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            college_id TEXT,
            college_name TEXT NOT NULL,
            major_name TEXT NOT NULL,
            province TEXT NOT NULL,
            subject_category TEXT,
            plan_count INTEGER,
            duration INTEGER,
            tuition INTEGER,
            remarks TEXT
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_admission_province_year
            ON admission_scores(province, year, subject_category);
        CREATE INDEX IF NOT EXISTS idx_admission_college
            ON admission_scores(college_id, year);
        CREATE INDEX IF NOT EXISTS idx_admission_score
            ON admission_scores(province, year, subject_category, min_score);
        CREATE INDEX IF NOT EXISTS idx_score_rank
            ON score_rank_table(year, province, subject_category, score);
        CREATE INDEX IF NOT EXISTS idx_enrollment_plan
            ON enrollment_plans(year, province, college_name);
        """)
    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    init_database()

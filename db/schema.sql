-- ============================================================
-- 基于 RAG 的 Java 程序课程辅导系统 · 数据库设计 v1.0
-- 字符集 utf8mb4，引擎 InnoDB
-- 说明：本文件与 backend 的 JPA 实体严格对应（ddl-auto=validate），
--       修改实体后必须同步修改本文件，否则应用启动失败。
-- ============================================================

CREATE DATABASE IF NOT EXISTS javacourse_kb
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE javacourse_kb;

-- ---------- 1. 账号与会话 ----------
CREATE TABLE IF NOT EXISTS user_accounts (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  account       VARCHAR(50)  NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  role          VARCHAR(20)  NOT NULL COMMENT 'STUDENT / TEACHER / ADMIN',
  display_name  VARCHAR(100) NOT NULL,
  student_id    BIGINT       NULL,
  enabled       BIT(1)       NOT NULL DEFAULT b'1',
  created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_accounts_account (account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录账号';

CREATE TABLE IF NOT EXISTS auth_sessions (
  token      VARCHAR(64)  NOT NULL,
  user_id    BIGINT       NOT NULL,
  expires_at DATETIME(6)  NOT NULL,
  created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (token),
  KEY idx_auth_sessions_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录会话';

CREATE TABLE IF NOT EXISTS students (
  id         BIGINT       NOT NULL AUTO_INCREMENT,
  student_no VARCHAR(255) NOT NULL,
  name       VARCHAR(255) NOT NULL,
  college    VARCHAR(255) NULL,
  major      VARCHAR(255) NULL,
  grade      VARCHAR(255) NULL,
  email      VARCHAR(255) NULL,
  created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_students_no (student_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生档案';

-- ---------- 2. 课程结构：课程 -> 章节 -> 知识点 ----------
CREATE TABLE IF NOT EXISTS courses (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  name        VARCHAR(200) NOT NULL,
  code        VARCHAR(50)  NULL,
  department  VARCHAR(255) NULL,
  semester    VARCHAR(255) NULL,
  description TEXT         NULL,
  created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_courses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程';

CREATE TABLE IF NOT EXISTS chapters (
  id         BIGINT       NOT NULL AUTO_INCREMENT,
  course_id  BIGINT       NOT NULL,
  chapter_no INT          NOT NULL,
  title      VARCHAR(200) NOT NULL,
  summary    TEXT         NULL,
  created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_chapters_course_no (course_id, chapter_no),
  CONSTRAINT fk_chapters_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='章节';

CREATE TABLE IF NOT EXISTS knowledge_points (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  course_id   BIGINT       NOT NULL,
  chapter_id  BIGINT       NULL,
  code        VARCHAR(50)  NOT NULL,
  name        VARCHAR(200) NOT NULL,
  description TEXT         NULL,
  difficulty  INT          NULL COMMENT '1-5',
  created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_kp_code (code),
  KEY idx_kp_chapter (chapter_id),
  CONSTRAINT fk_kp_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
  CONSTRAINT fk_kp_chapter FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点（检索与错题溯源的最小单元）';

-- ---------- 3. 题库与判分 ----------
CREATE TABLE IF NOT EXISTS questions (
  id                 BIGINT      NOT NULL AUTO_INCREMENT,
  course_id          BIGINT      NOT NULL,
  chapter_id         BIGINT      NULL,
  knowledge_point_id BIGINT      NULL,
  type               VARCHAR(20) NOT NULL COMMENT 'CHOICE/MULTI/JUDGE/FILL/CODE',
  stem               TEXT        NOT NULL,
  options_json       TEXT        NULL,
  answer             TEXT        NULL,
  analysis           TEXT        NULL,
  difficulty         INT         NULL,
  source             VARCHAR(200) NULL,
  created_at         DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_questions_kp (knowledge_point_id),
  KEY idx_questions_course (course_id),
  CONSTRAINT fk_questions_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
  CONSTRAINT fk_questions_chapter FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL,
  CONSTRAINT fk_questions_kp FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目';

CREATE TABLE IF NOT EXISTS answer_records (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  user_id     BIGINT      NOT NULL,
  question_id BIGINT      NOT NULL,
  user_answer TEXT        NULL,
  is_correct  BIT(1)      NOT NULL,
  score       INT         NULL,
  created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_answer_user (user_id),
  KEY idx_answer_question (question_id),
  CONSTRAINT fk_answer_question FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='答题记录（判分与错题溯源）';

-- ---------- 4. 报错诊断 ----------
CREATE TABLE IF NOT EXISTS error_cases (
  id                 BIGINT       NOT NULL AUTO_INCREMENT,
  error_code         VARCHAR(100) NOT NULL,
  category           VARCHAR(50)  NULL,
  javac_pattern      TEXT         NULL,
  cause              TEXT         NULL,
  solution           TEXT         NULL,
  knowledge_point_id BIGINT       NULL,
  example_code       TEXT         NULL,
  created_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_error_code (error_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='编译/运行错误案例库';

CREATE TABLE IF NOT EXISTS diagnostic_records (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  user_id         BIGINT       NULL,
  raw_error       TEXT         NOT NULL,
  matched_case_id BIGINT       NULL,
  confidence      DOUBLE       NULL,
  suggestion      TEXT         NULL,
  created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_diag_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='诊断记录（用于评估诊断准确率）';

-- ---------- 5. 知识库文档与问答 ----------
CREATE TABLE IF NOT EXISTS documents (
  id         BIGINT       NOT NULL AUTO_INCREMENT,
  course_id  BIGINT       NOT NULL,
  file_name  VARCHAR(500) NOT NULL,
  file_size  BIGINT       NULL,
  doc_type   VARCHAR(255) NULL DEFAULT 'other',
  status     VARCHAR(255) NULL DEFAULT 'processing',
  task_id    VARCHAR(255) NULL,
  created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_documents_course (course_id),
  CONSTRAINT fk_documents_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档';

CREATE TABLE IF NOT EXISTS chat_histories (
  id           BIGINT      NOT NULL AUTO_INCREMENT,
  student_id   BIGINT      NOT NULL,
  question     TEXT        NOT NULL,
  answer       LONGTEXT    NULL,
  category     VARCHAR(255) NULL,
  sources_json LONGTEXT    NULL,
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_chat_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问答历史';

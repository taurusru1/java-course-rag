package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 编译/运行错误案例库：javac 报错文本 -> 成因 -> 修复建议 -> 关联知识点。 */
@Entity @Table(name = "error_cases")
public class ErrorCase {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    /** 归一化后的报错码，例如 cannot_find_symbol / incompatible_types。 */
    @Column(name = "error_code", nullable = false, unique = true, length = 100) private String errorCode;
    @Column(length = 50) private String category;
    /** 用于匹配原始报错的正则或关键片段。 */
    @Column(name = "javac_pattern", columnDefinition = "TEXT") private String javacPattern;
    @Column(columnDefinition = "TEXT") private String cause;
    @Column(columnDefinition = "TEXT") private String solution;
    @Column(name = "knowledge_point_id") private Long knowledgePointId;
    @Column(name = "example_code", columnDefinition = "TEXT") private String exampleCode;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public String getErrorCode(){return errorCode;} public void setErrorCode(String v){errorCode=v;}
    public String getCategory(){return category;} public void setCategory(String v){category=v;}
    public String getJavacPattern(){return javacPattern;} public void setJavacPattern(String v){javacPattern=v;}
    public String getCause(){return cause;} public void setCause(String v){cause=v;}
    public String getSolution(){return solution;} public void setSolution(String v){solution=v;}
    public Long getKnowledgePointId(){return knowledgePointId;} public void setKnowledgePointId(Long v){knowledgePointId=v;}
    public String getExampleCode(){return exampleCode;} public void setExampleCode(String v){exampleCode=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

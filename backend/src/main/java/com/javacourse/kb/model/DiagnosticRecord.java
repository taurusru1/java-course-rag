package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 诊断记录：学生粘贴的报错原文、命中的案例与最终建议，用于评估诊断准确率。 */
@Entity @Table(name = "diagnostic_records")
public class DiagnosticRecord {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "user_id") private Long userId;
    @Column(name = "raw_error", nullable = false, columnDefinition = "TEXT") private String rawError;
    @Column(name = "matched_case_id") private Long matchedCaseId;
    /** 匹配置信度 0-1，低于阈值时降级为通用检索。 */
    private Double confidence;
    @Column(columnDefinition = "TEXT") private String suggestion;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Long getUserId(){return userId;} public void setUserId(Long v){userId=v;}
    public String getRawError(){return rawError;} public void setRawError(String v){rawError=v;}
    public Long getMatchedCaseId(){return matchedCaseId;} public void setMatchedCaseId(Long v){matchedCaseId=v;}
    public Double getConfidence(){return confidence;} public void setConfidence(Double v){confidence=v;}
    public String getSuggestion(){return suggestion;} public void setSuggestion(String v){suggestion=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

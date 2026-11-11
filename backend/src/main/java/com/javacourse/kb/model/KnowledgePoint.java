package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 知识点：检索与错题溯源的最小语义单元。 */
@Entity @Table(name = "knowledge_points")
public class KnowledgePoint {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "course_id", nullable = false) private Long courseId;
    @Column(name = "chapter_id") private Long chapterId;
    @Column(nullable = false, unique = true, length = 50) private String code;
    @Column(nullable = false, length = 200) private String name;
    @Column(columnDefinition = "TEXT") private String description;
    /** 难度 1-5，用于自适应出题与错题分析。 */
    private Integer difficulty;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Long getCourseId(){return courseId;} public void setCourseId(Long v){courseId=v;}
    public Long getChapterId(){return chapterId;} public void setChapterId(Long v){chapterId=v;}
    public String getCode(){return code;} public void setCode(String v){code=v;}
    public String getName(){return name;} public void setName(String v){name=v;}
    public String getDescription(){return description;} public void setDescription(String v){description=v;}
    public Integer getDifficulty(){return difficulty;} public void setDifficulty(Integer v){difficulty=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

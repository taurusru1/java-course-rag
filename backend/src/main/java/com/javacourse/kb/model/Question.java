package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 题目：CHOICE 单选 / MULTI 多选 / JUDGE 判断 / FILL 填空 / CODE 编程题。 */
@Entity @Table(name = "questions")
public class Question {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "course_id", nullable = false) private Long courseId;
    @Column(name = "chapter_id") private Long chapterId;
    @Column(name = "knowledge_point_id") private Long knowledgePointId;
    @Column(nullable = false, length = 20) private String type;
    @Column(nullable = false, columnDefinition = "TEXT") private String stem;
    @Column(name = "options_json", columnDefinition = "TEXT") private String optionsJson;
    @Column(columnDefinition = "TEXT") private String answer;
    @Column(columnDefinition = "TEXT") private String analysis;
    private Integer difficulty;
    /** 来源：自建题库 / 教材习题 / 转换自公开题库。 */
    @Column(length = 200) private String source;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Long getCourseId(){return courseId;} public void setCourseId(Long v){courseId=v;}
    public Long getChapterId(){return chapterId;} public void setChapterId(Long v){chapterId=v;}
    public Long getKnowledgePointId(){return knowledgePointId;} public void setKnowledgePointId(Long v){knowledgePointId=v;}
    public String getType(){return type;} public void setType(String v){type=v;}
    public String getStem(){return stem;} public void setStem(String v){stem=v;}
    public String getOptionsJson(){return optionsJson;} public void setOptionsJson(String v){optionsJson=v;}
    public String getAnswer(){return answer;} public void setAnswer(String v){answer=v;}
    public String getAnalysis(){return analysis;} public void setAnalysis(String v){analysis=v;}
    public Integer getDifficulty(){return difficulty;} public void setDifficulty(Integer v){difficulty=v;}
    public String getSource(){return source;} public void setSource(String v){source=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

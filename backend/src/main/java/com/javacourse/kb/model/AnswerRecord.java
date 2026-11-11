package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 答题记录：判分结果 + 错题溯源的数据基础。 */
@Entity @Table(name = "answer_records")
public class AnswerRecord {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "user_id", nullable = false) private Long userId;
    @Column(name = "question_id", nullable = false) private Long questionId;
    @Column(name = "user_answer", columnDefinition = "TEXT") private String userAnswer;
    @Column(name = "is_correct", nullable = false) private Boolean correct;
    /** 编程题按测试用例通过率给分，其他题型 0/100。 */
    private Integer score;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Long getUserId(){return userId;} public void setUserId(Long v){userId=v;}
    public Long getQuestionId(){return questionId;} public void setQuestionId(Long v){questionId=v;}
    public String getUserAnswer(){return userAnswer;} public void setUserAnswer(String v){userAnswer=v;}
    public Boolean getCorrect(){return correct;} public void setCorrect(Boolean v){correct=v;}
    public Integer getScore(){return score;} public void setScore(Integer v){score=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

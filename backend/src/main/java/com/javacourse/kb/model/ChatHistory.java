package com.javacourse.kb.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity @Table(name="chat_histories")
public class ChatHistory {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(name="student_id",nullable=false) private Long studentId;
 @Column(nullable=false,columnDefinition="TEXT") private String question; @Column(columnDefinition="LONGTEXT") private String answer;
 private String category; @Column(name="sources_json",columnDefinition="LONGTEXT") private String sourcesJson;
 @Column(name="created_at",insertable=false,updatable=false) private LocalDateTime createdAt;
 public Long getId(){return id;} public Long getStudentId(){return studentId;} public void setStudentId(Long v){studentId=v;}
 public String getQuestion(){return question;} public void setQuestion(String v){question=v;} public String getAnswer(){return answer;} public void setAnswer(String v){answer=v;}
 public String getCategory(){return category;} public void setCategory(String v){category=v;} public String getSourcesJson(){return sourcesJson;} public void setSourcesJson(String v){sourcesJson=v;}
 public LocalDateTime getCreatedAt(){return createdAt;}
}

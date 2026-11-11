package com.javacourse.kb.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity @Table(name="student_favorites")
public class StudentFavorite {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(name="student_id",nullable=false) private Long studentId; @Column(name="history_id") private Long historyId;
 @Column(nullable=false) private String title; @Column(name="item_type",nullable=false) private String itemType; private String source;
 @Column(name="created_at",insertable=false,updatable=false) private LocalDateTime createdAt;
 public Long getId(){return id;} public Long getStudentId(){return studentId;} public void setStudentId(Long v){studentId=v;}
 public Long getHistoryId(){return historyId;} public void setHistoryId(Long v){historyId=v;} public String getTitle(){return title;} public void setTitle(String v){title=v;}
 public String getItemType(){return itemType;} public void setItemType(String v){itemType=v;} public String getSource(){return source;} public void setSource(String v){source=v;}
 public LocalDateTime getCreatedAt(){return createdAt;}
}

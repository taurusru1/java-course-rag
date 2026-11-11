package com.javacourse.kb.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity @Table(name="campus_notices")
public class CampusNotice {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(nullable=false) private String title; @Column(nullable=false) private String category; @Column(nullable=false) private String department;
 @Column(nullable=false,columnDefinition="TEXT") private String content; private Boolean important;
 @Column(name="published_at") private LocalDateTime publishedAt;
 public Long getId(){return id;} public String getTitle(){return title;} public String getCategory(){return category;} public String getDepartment(){return department;}
 public String getContent(){return content;} public Boolean getImportant(){return important;} public LocalDateTime getPublishedAt(){return publishedAt;}
}

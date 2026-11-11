package com.javacourse.kb.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity @Table(name="students")
public class Student {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(name="student_no",nullable=false,unique=true) private String studentNo;
 @Column(nullable=false) private String name; private String college; private String major; private String grade; private String email;
 @Column(name="created_at",insertable=false,updatable=false) private LocalDateTime createdAt;
 @Column(name="updated_at",insertable=false,updatable=false) private LocalDateTime updatedAt;
 public Long getId(){return id;} public String getStudentNo(){return studentNo;} public void setStudentNo(String v){studentNo=v;}
 public String getName(){return name;} public void setName(String v){name=v;} public String getCollege(){return college;} public void setCollege(String v){college=v;}
 public String getMajor(){return major;} public void setMajor(String v){major=v;} public String getGrade(){return grade;} public void setGrade(String v){grade=v;}
 public String getEmail(){return email;} public void setEmail(String v){email=v;} public LocalDateTime getCreatedAt(){return createdAt;} public LocalDateTime getUpdatedAt(){return updatedAt;}
}

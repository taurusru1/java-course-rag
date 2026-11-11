package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity @Table(name = "courses")
public class Course {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(nullable = false, length = 200) private String name;
    @Column(unique = true, length = 50) private String code;
    private String department;
    private String semester;
    @Column(columnDefinition = "TEXT") private String description;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public String getName(){return name;} public void setName(String v){name=v;}
    public String getCode(){return code;} public void setCode(String v){code=v;} public String getDepartment(){return department;}
    public void setDepartment(String v){department=v;} public String getSemester(){return semester;} public void setSemester(String v){semester=v;}
    public String getDescription(){return description;} public void setDescription(String v){description=v;} public LocalDateTime getCreatedAt(){return createdAt;}
}

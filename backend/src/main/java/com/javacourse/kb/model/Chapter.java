package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/** 课程章节：课程 -> 章节 -> 知识点 三级导航的中间层。 */
@Entity @Table(name = "chapters")
public class Chapter {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "course_id", nullable = false) private Long courseId;
    @Column(name = "chapter_no", nullable = false) private Integer chapterNo;
    @Column(nullable = false, length = 200) private String title;
    @Column(columnDefinition = "TEXT") private String summary;
    @Column(name = "created_at", insertable = false, updatable = false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Long getCourseId(){return courseId;} public void setCourseId(Long v){courseId=v;}
    public Integer getChapterNo(){return chapterNo;} public void setChapterNo(Integer v){chapterNo=v;}
    public String getTitle(){return title;} public void setTitle(String v){title=v;}
    public String getSummary(){return summary;} public void setSummary(String v){summary=v;}
    public LocalDateTime getCreatedAt(){return createdAt;}
}

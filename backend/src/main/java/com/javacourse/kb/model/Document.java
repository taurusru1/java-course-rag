package com.javacourse.kb.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity @Table(name = "documents")
public class Document {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(optional=false, fetch=FetchType.LAZY) @JoinColumn(name="course_id") private Course course;
    @Column(name="file_name", nullable=false, length=500) private String fileName;
    @Column(name="file_size") private Long fileSize;
    @Column(name="doc_type") private String docType = "other";
    private String status = "processing";
    @Column(name="task_id") private String taskId;
    @Column(name="created_at", insertable=false, updatable=false) private LocalDateTime createdAt;
    public Long getId(){return id;} public Course getCourse(){return course;} public void setCourse(Course v){course=v;}
    public String getFileName(){return fileName;} public void setFileName(String v){fileName=v;} public Long getFileSize(){return fileSize;}
    public void setFileSize(Long v){fileSize=v;} public String getDocType(){return docType;} public void setDocType(String v){docType=v;}
    public String getStatus(){return status;} public void setStatus(String v){status=v;} public String getTaskId(){return taskId;}
    public void setTaskId(String v){taskId=v;} public LocalDateTime getCreatedAt(){return createdAt;}
}

package com.javacourse.kb.model;
import jakarta.persistence.*;
@Entity @Table(name="knowledge_categories")
public class KnowledgeCategory {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(nullable=false,unique=true) private String code; @Column(nullable=false) private String name;
 private String department; private String description; @Column(name="document_count") private Integer documentCount;
 @Column(name="sort_order") private Integer sortOrder; private Boolean enabled;
 public Long getId(){return id;} public String getCode(){return code;} public String getName(){return name;} public String getDepartment(){return department;}
 public String getDescription(){return description;} public Integer getDocumentCount(){return documentCount;} public Integer getSortOrder(){return sortOrder;} public Boolean getEnabled(){return enabled;}
}

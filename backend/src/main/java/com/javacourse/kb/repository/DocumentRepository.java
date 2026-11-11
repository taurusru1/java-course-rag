package com.javacourse.kb.repository;
import com.javacourse.kb.model.Document;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
public interface DocumentRepository extends JpaRepository<Document, Long> {
    List<Document> findByCourseIdOrderByCreatedAtDesc(Long courseId);
    List<Document> findTop8ByOrderByCreatedAtDesc();
    long countByStatus(String status);
    long countByCourseId(Long courseId);
}

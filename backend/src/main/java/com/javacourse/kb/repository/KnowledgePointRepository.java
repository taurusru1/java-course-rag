package com.javacourse.kb.repository;

import com.javacourse.kb.model.KnowledgePoint;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KnowledgePointRepository extends JpaRepository<KnowledgePoint,Long> {
    List<KnowledgePoint> findByCourseIdOrderByIdAsc(Long courseId);
    List<KnowledgePoint> findByChapterIdOrderByIdAsc(Long chapterId);
    Optional<KnowledgePoint> findByCode(String code);
}

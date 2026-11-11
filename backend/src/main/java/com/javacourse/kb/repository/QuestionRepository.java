package com.javacourse.kb.repository;

import com.javacourse.kb.model.Question;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QuestionRepository extends JpaRepository<Question,Long> {
    List<Question> findByCourseIdOrderByIdAsc(Long courseId);
    List<Question> findByKnowledgePointIdOrderByIdAsc(Long knowledgePointId);
    List<Question> findByTypeOrderByIdAsc(String type);
}

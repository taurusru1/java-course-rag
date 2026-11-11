package com.javacourse.kb.repository;

import com.javacourse.kb.model.Chapter;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChapterRepository extends JpaRepository<Chapter,Long> {
    List<Chapter> findByCourseIdOrderByChapterNoAsc(Long courseId);
}

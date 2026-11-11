package com.javacourse.kb.repository;

import com.javacourse.kb.model.AnswerRecord;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AnswerRecordRepository extends JpaRepository<AnswerRecord,Long> {
    List<AnswerRecord> findByUserIdOrderByCreatedAtDesc(Long userId);
    List<AnswerRecord> findByUserIdAndCorrectFalseOrderByCreatedAtDesc(Long userId);
    long countByUserId(Long userId);
    long countByUserIdAndCorrectFalse(Long userId);
}
